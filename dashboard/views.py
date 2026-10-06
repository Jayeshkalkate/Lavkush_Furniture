import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from gallery.models import Category, ImageWithCaption, Rating
from gallery.views import import_products_from_file
from lavkushfurniture.utils import safe_next_url
from order.email_utils import send_order_event_email
from order.models import Coupon, Order, OrderItem, Payment
from team.models import TeamMember

from .forms import BulkUploadForm, CategoryForm, CouponForm, DashboardProductForm, OrderUpdateForm

logger = logging.getLogger(__name__)

staff_required = user_passes_test(lambda u: u.is_authenticated and u.is_active and u.is_staff, login_url='login')
superuser_required = user_passes_test(lambda u: u.is_authenticated and u.is_active and u.is_superuser, login_url='login')

LIVE_STATUSES = ['processing', 'shipped', 'delivered']


def _paginate(request, queryset, per_page=15):
    page = Paginator(queryset, per_page).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return page, params.urlencode()


def _back(request, fallback):
    return redirect(safe_next_url(request, request.POST.get('next'), reverse(fallback)))


def _money(qs, field='amount'):
    return qs.aggregate(v=Sum(field))['v'] or Decimal('0.00')


# ---------------------------------------------------------------- overview
@staff_required
def home(request):
    today = timezone.localdate()
    paid = Payment.objects.filter(status='paid')
    days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        days.append({'label': d.strftime('%a'), 'amount': _money(paid.filter(created_at__date=d))})
    peak = max([x['amount'] for x in days] + [Decimal('1')])
    for x in days:
        x['pct'] = int(x['amount'] * 100 / peak) if x['amount'] else 0

    live_orders = Order.objects.filter(order_status__in=LIVE_STATUSES)
    line_total = ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField(max_digits=14, decimal_places=2))
    top_products = (OrderItem.objects.filter(order__order_status__in=LIVE_STATUSES)
                    .values('product_name').annotate(units=Sum('quantity'), revenue=Sum(line_total)).order_by('-units')[:5])
    active_products = ImageWithCaption.objects.filter(is_active=True)
    context = {
        'active': 'home',
        'revenue_total': _money(paid),
        'revenue_today': _money(paid.filter(created_at__date=today)),
        'revenue_month': _money(paid.filter(created_at__year=today.year, created_at__month=today.month)),
        'refunded': _money(Payment.objects.filter(status__in=['refunded']), 'refund_amount'),
        'orders_total': live_orders.count(),
        'to_process': Order.objects.filter(order_status='processing').count(),
        'to_deliver': Order.objects.filter(order_status='shipped').count(),
        'returns_open': Order.objects.filter(return_status='requested').count(),
        'customers': User.objects.filter(is_staff=False).count(),
        'new_customers': User.objects.filter(is_staff=False, date_joined__year=today.year, date_joined__month=today.month).count(),
        'products_count': ImageWithCaption.objects.count(),
        'out_of_stock': active_products.filter(stock_quantity=0).count(),
        'low_stock': active_products.filter(stock_quantity__gt=0, stock_quantity__lte=3).order_by('stock_quantity')[:6],
        'days': days,
        'top_products': top_products,
        'recent_orders': Order.objects.exclude(order_status='payment_pending').select_related('user')[:8],
        'health': [
            ('Online payments (Razorpay)', bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)),
            ('Payment webhook secret', bool(settings.RAZORPAY_WEBHOOK_SECRET)),
            ('Image storage (Cloudinary)', bool(settings.USE_CLOUDINARY)),
            ('Order emails (SMTP)', 'smtp' in settings.EMAIL_BACKEND.lower()),
        ],
    }
    return render(request, 'dashboard/home.html', context)


# ---------------------------------------------------------------- products
@staff_required
def products(request):
    qs = ImageWithCaption.objects.select_related('category').order_by('-uploaded_at')
    q = request.GET.get('q', '').strip()
    cat = request.GET.get('category', '').strip()
    status = request.GET.get('status', '').strip()
    if q:
        qs = qs.filter(Q(caption__icontains=q) | Q(sku__icontains=q) | Q(materials__icontains=q) | Q(color__icontains=q))
    if cat.isdigit():
        qs = qs.filter(category_id=int(cat))
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'hidden':
        qs = qs.filter(is_active=False)
    elif status == 'out':
        qs = qs.filter(stock_quantity=0)
    elif status == 'low':
        qs = qs.filter(stock_quantity__gt=0, stock_quantity__lte=3)
    elif status == 'featured':
        qs = qs.filter(is_featured=True)
    page, qstring = _paginate(request, qs)
    return render(request, 'dashboard/products.html', {
        'active': 'products', 'page_obj': page, 'qs': qstring, 'q': q, 'cat': cat, 'status': status,
        'categories': Category.objects.all(),
    })


def _product_form(request, product=None):
    form = DashboardProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        try:
            obj = form.save()
        except Exception as exc:  # e.g. image storage not configured
            logger.exception('Product save failed')
            form.add_error(None, f'Could not save the product (is image storage configured?): {exc}')
        else:
            messages.success(request, f"'{obj.caption}' saved.")
            return redirect('dashboard:products')
    return render(request, 'dashboard/product_form.html', {'active': 'products', 'form': form, 'product': product})


@staff_required
def product_add(request):
    return _product_form(request)


@staff_required
def product_edit(request, pk):
    return _product_form(request, get_object_or_404(ImageWithCaption, pk=pk))


@staff_required
@require_POST
def product_quick_update(request, pk):
    product = get_object_or_404(ImageWithCaption, pk=pk)
    try:
        price = Decimal(request.POST.get('price', '').replace(',', '').strip())
        stock = int(request.POST.get('stock_quantity', ''))
        if price < 0 or stock < 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        messages.error(request, 'Enter a valid price and stock (zero or more).')
    else:
        product.price, product.stock_quantity = price, stock
        product.save(update_fields=['price', 'stock_quantity', 'updated_at'])
        messages.success(request, f"Updated '{product.caption}'.")
    return _back(request, 'dashboard:products')


@staff_required
@require_POST
def product_toggle(request, pk):
    product = get_object_or_404(ImageWithCaption, pk=pk)
    field = request.POST.get('field')
    if field in {'is_active', 'is_featured'}:
        setattr(product, field, not getattr(product, field))
        product.save(update_fields=[field, 'updated_at'])
        messages.success(request, f"'{product.caption}' updated.")
    return _back(request, 'dashboard:products')


@superuser_required
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(ImageWithCaption, pk=pk)
    name = product.caption
    product.delete()
    messages.success(request, f"'{name}' deleted. Past orders keep their own copy of the details.")
    return redirect('dashboard:products')


@staff_required
def bulk_upload(request):
    form = BulkUploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        try:
            count = import_products_from_file(request.FILES['file'])
        except Exception as exc:
            logger.exception('Bulk import failed')
            form.add_error('file', str(exc))
        else:
            messages.success(request, f'{count} products imported.')
            return redirect('dashboard:products')
    return render(request, 'dashboard/bulk_upload.html', {'active': 'products', 'form': form})


# -------------------------------------------------------------- categories
@staff_required
def categories(request):
    qs = Category.objects.annotate(product_total=Count('products'))
    return render(request, 'dashboard/categories.html', {'active': 'categories', 'categories': qs})


def _unique_category_slug(name, exclude_pk=None):
    base = slugify(name) or 'category'
    slug, n = base, 2
    while Category.objects.filter(slug=slug).exclude(pk=exclude_pk).exists():
        slug = f'{base}-{n}'
        n += 1
    return slug


def _category_form(request, category=None):
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        if not obj.slug:
            obj.slug = _unique_category_slug(obj.name, obj.pk)
        obj.save()
        messages.success(request, f"Category '{obj.name}' saved.")
        return redirect('dashboard:categories')
    return render(request, 'dashboard/category_form.html', {'active': 'categories', 'form': form, 'category': category})


@staff_required
def category_add(request):
    return _category_form(request)


@staff_required
def category_edit(request, pk):
    return _category_form(request, get_object_or_404(Category, pk=pk))


@superuser_required
@require_POST
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.success(request, 'Category deleted. Its products are now uncategorised.')
    return redirect('dashboard:categories')


# ------------------------------------------------------------------ orders
@staff_required
def orders(request):
    qs = Order.objects.select_related('user').order_by('-created_at')
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    if q:
        qs = qs.filter(Q(invoice_number__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q) |
                       Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(user__username__icontains=q) |
                       Q(tracking_number__icontains=q))
    if status:
        qs = qs.filter(order_status=status)
    elif request.GET.get('all') != '1':
        qs = qs.exclude(order_status='payment_pending')
    page, qstring = _paginate(request, qs)
    return render(request, 'dashboard/orders.html', {
        'active': 'orders', 'page_obj': page, 'qs': qstring, 'q': q, 'status': status,
        'status_choices': Order.ORDER_STATUS,
    })


@staff_required
def order_detail(request, invoice_number):
    order = get_object_or_404(Order.objects.select_related('user', 'payment').prefetch_related('items'), invoice_number=invoice_number)
    old_status = order.order_status
    form = OrderUpdateForm(request.POST or None, instance=order)
    if request.method == 'POST' and form.is_valid():
        new_status = form.cleaned_data['order_status']
        paid = bool(order.payment_id and order.payment and order.payment.status == 'paid')
        if new_status == 'cancelled' and old_status != 'cancelled' and paid:
            form.add_error('order_status', 'This order is paid. Use the Refund button to cancel it and return the money.')
        else:
            obj = form.save(commit=False)
            now = timezone.now()
            if new_status == 'shipped' and not obj.shipped_at:
                obj.shipped_at = now
            if new_status == 'delivered':
                obj.delivered_at = obj.delivered_at or now
                obj.shipped_at = obj.shipped_at or now
            if new_status == 'cancelled' and not obj.cancellation_reason:
                obj.cancellation_reason = 'Cancelled by staff.'
            obj.return_requested = obj.return_status != 'none'
            obj.save()
            if new_status != old_status and new_status in {'shipped', 'delivered', 'cancelled', 'return_pending', 'returned'}:
                transaction.on_commit(lambda: send_order_event_email(obj, new_status))
            messages.success(request, 'Order updated.')
            return redirect('dashboard:order_detail', invoice_number=order.invoice_number)
    can_refund = bool(order.payment and order.payment.status == 'paid' and order.payment.payment_id)
    return render(request, 'dashboard/order_detail.html', {'active': 'orders', 'order': order, 'form': form, 'can_refund': can_refund})


@staff_required
def payments(request):
    qs = Payment.objects.select_related('user', 'order').order_by('-created_at')
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    if q:
        qs = qs.filter(Q(payment_id__icontains=q) | Q(order_id__icontains=q) | Q(user__username__icontains=q) | Q(order__invoice_number__icontains=q))
    if status:
        qs = qs.filter(status=status)
    page, qstring = _paginate(request, qs)
    return render(request, 'dashboard/payments.html', {
        'active': 'payments', 'page_obj': page, 'qs': qstring, 'q': q, 'status': status,
        'status_choices': Payment.STATUS_CHOICES,
        'total_paid': _money(Payment.objects.filter(status='paid')),
        'total_refunded': _money(Payment.objects.filter(status='refunded'), 'refund_amount'),
        'failed_count': Payment.objects.filter(status='failed').count(),
    })


# --------------------------------------------------------------- customers
@staff_required
def customers(request):
    qs = (User.objects.filter(is_staff=False).select_related('items')
          .annotate(order_count=Count('orders', distinct=True),
                    spent=Sum('orders__total_amount', filter=Q(orders__order_status__in=LIVE_STATUSES)))
          .order_by('-date_joined'))
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q) |
                       Q(last_name__icontains=q) | Q(items__phone_number__icontains=q))
    page, qstring = _paginate(request, qs)
    return render(request, 'dashboard/customers.html', {'active': 'customers', 'page_obj': page, 'qs': qstring, 'q': q})


@staff_required
@require_POST
def customer_toggle(request, pk):
    user = get_object_or_404(User, pk=pk, is_staff=False)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    messages.success(request, f"{user.username} is now {'active' if user.is_active else 'blocked'}.")
    return _back(request, 'dashboard:customers')


# ----------------------------------------------------------------- coupons
@staff_required
def coupons(request):
    return render(request, 'dashboard/coupons.html', {'active': 'coupons', 'coupons': Coupon.objects.all()})


def _coupon_form(request, coupon=None):
    form = CouponForm(request.POST or None, instance=coupon)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Coupon saved.')
        return redirect('dashboard:coupons')
    return render(request, 'dashboard/coupon_form.html', {'active': 'coupons', 'form': form, 'coupon': coupon})


@staff_required
def coupon_add(request):
    return _coupon_form(request)


@staff_required
def coupon_edit(request, pk):
    return _coupon_form(request, get_object_or_404(Coupon, pk=pk))


@staff_required
@require_POST
def coupon_toggle(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.active = not coupon.active
    coupon.save(update_fields=['active'])
    messages.success(request, f"Coupon {coupon.code} is now {'active' if coupon.active else 'paused'}.")
    return redirect('dashboard:coupons')


@staff_required
@require_POST
def coupon_delete(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.delete()
    messages.success(request, 'Coupon deleted.')
    return redirect('dashboard:coupons')


# ------------------------------------------------------------- reviews/team
@staff_required
def reviews(request):
    qs = Rating.objects.select_related('user', 'item').order_by('-created_at')
    status = request.GET.get('status', '').strip()
    if status == 'visible':
        qs = qs.filter(approved=True)
    elif status == 'hidden':
        qs = qs.filter(approved=False)
    page, qstring = _paginate(request, qs)
    return render(request, 'dashboard/reviews.html', {'active': 'reviews', 'page_obj': page, 'qs': qstring, 'status': status})


@staff_required
@require_POST
def review_toggle(request, pk):
    review = get_object_or_404(Rating, pk=pk)
    review.approved = not review.approved
    review.save(update_fields=['approved', 'updated_at'])
    messages.success(request, 'Review is now ' + ('visible.' if review.approved else 'hidden.'))
    return _back(request, 'dashboard:reviews')


@staff_required
@require_POST
def review_delete(request, pk):
    get_object_or_404(Rating, pk=pk).delete()
    messages.success(request, 'Review deleted.')
    return _back(request, 'dashboard:reviews')


@staff_required
def team(request):
    return render(request, 'dashboard/team.html', {'active': 'team', 'members': TeamMember.objects.all()})
