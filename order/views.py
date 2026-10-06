import hashlib
import hmac
import json
import logging
from datetime import timedelta
from decimal import Decimal

import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Avg, Count, Sum, F, DecimalField, ExpressionWrapper
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from xml.sax.saxutils import escape as xml_escape

from cart.models import Cart
from gallery.models import ImageWithCaption
from lavkushfurniture.utils import safe_next_url
from .forms import CheckoutForm
from .email_utils import send_order_event_email
from .models import Coupon, Order, OrderItem, Payment

logger = logging.getLogger(__name__)


def _admin(user):
    return user.is_staff


def _get_client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise RuntimeError('Razorpay is not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.')
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def _calculate_totals(items, coupon=None):
    subtotal = sum((item.subtotal for item in items), Decimal('0.00'))
    shipping = Decimal(str(settings.SHIPPING_FLAT_RATE)) if subtotal > 0 else Decimal('0.00')
    discount = coupon.discount_for(subtotal) if coupon else Decimal('0.00')
    taxable = max(subtotal - discount, Decimal('0.00'))
    tax = (taxable * Decimal(str(settings.GST_RATE)) / Decimal('100')).quantize(Decimal('0.01'))
    total = taxable + shipping + tax
    return subtotal, shipping, tax, discount, total


def _send_order_email(order):
    send_order_event_email(order, 'confirmed', f'Total: ₹{order.total_amount:.2f}')


def _deduct_inventory(order):
    if order.inventory_deducted:
        return True
    items = list(order.items.select_related('product').all())
    for item in items:
        if not item.product_id:
            continue
        product = ImageWithCaption.objects.select_for_update().get(pk=item.product_id)
        if product.stock_quantity < item.quantity:
            return False
    for item in items:
        if not item.product_id:
            continue
        product = ImageWithCaption.objects.select_for_update().get(pk=item.product_id)
        product.stock_quantity -= item.quantity
        product.save(update_fields=['stock_quantity', 'updated_at'])
    order.inventory_deducted = True
    order.save(update_fields=['inventory_deducted', 'updated_at'])
    return True


def _finalize_paid_payment(payment, payment_id=None, signature=None, gateway_payload=None):
    with transaction.atomic():
        payment = Payment.objects.select_for_update().select_related('order').get(pk=payment.pk)
        order = payment.order
        if payment.status == 'refunded':
            return order
        payment.status = 'paid'
        payment.payment_id = payment_id or payment.payment_id
        payment.signature = signature or payment.signature
        payment.paid_at = payment.paid_at or timezone.now()
        if gateway_payload:
            payment.gateway_response = gateway_payload
            payment.gateway_status = gateway_payload.get('status', payment.gateway_status)
        payment.save(update_fields=['status', 'payment_id', 'signature', 'paid_at', 'gateway_response', 'gateway_status'])
        coupon_code = (order.coupon_code or '').strip().upper()
        if coupon_code:
            coupon = Coupon.objects.select_for_update().filter(code=coupon_code).first()
            if coupon:
                # The discount was already applied to the amount the customer paid,
                # so always honour it and just record the usage.
                coupon.uses += 1
                coupon.save(update_fields=['uses'])
        if not _deduct_inventory(order):
            raise ValueError('One or more items are no longer available in the requested quantity.')
        order.order_status = 'processing'
        order.save(update_fields=['order_status', 'updated_at'])
        transaction.on_commit(lambda: _send_order_email(order))
        return order


@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = list(cart.items.select_related('product').all())
    if not cart_items:
        messages.info(request, 'Your cart is empty.')
        return redirect('cart:view_cart')
    unavailable = [item.product.caption for item in cart_items if not item.product.is_active or item.product.stock_quantity < item.quantity]
    if unavailable:
        messages.error(request, f"Please update unavailable items before checkout: {', '.join(unavailable[:3])}.")
        return redirect('cart:view_cart')
    subtotal, shipping, tax, discount, total = _calculate_totals(cart_items)
    profile = getattr(request.user, 'items', None)
    initial = {
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'email': request.user.email,
        'phone': getattr(profile, 'phone_number', ''),
        'shipping_address': getattr(profile, 'address', ''),
        'city': getattr(profile, 'city', ''),
        'country': 'India',
    }
    form = CheckoutForm(request.POST or None, initial=initial if request.method != 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        try:
            coupon = getattr(form, 'coupon', None)
            if coupon and not coupon.is_valid(subtotal):
                form.add_error('coupon_code', 'This coupon is not valid for the current cart total.')
                return render(request, 'checkout.html', {'form': form, 'cart_items': cart_items, 'subtotal': subtotal, 'shipping': shipping, 'tax': tax, 'discount': Decimal('0.00'), 'total': subtotal + shipping + tax})
            subtotal, shipping, tax, discount, total = _calculate_totals(cart_items, coupon)
            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user
                order.coupon_code = coupon.code if coupon else ''
                order.subtotal = subtotal
                order.shipping_amount = shipping
                order.tax_amount = tax
                order.discount_amount = discount
                order.total_amount = total
                order.order_status = 'payment_pending'
                order.save()
                for cart_item in cart_items:
                    OrderItem.objects.create(order=order, product=cart_item.product, product_name=cart_item.product.caption, sku=cart_item.product.sku or '', price=cart_item.product.price, quantity=cart_item.quantity)
                client = _get_client()
                rzp_order = client.order.create({'amount': int((total * 100).quantize(Decimal('1'))), 'currency': 'INR', 'receipt': order.invoice_number, 'notes': {'order': order.invoice_number, 'user': request.user.username}})
                payment = Payment.objects.create(user=request.user, order_id=rzp_order['id'], amount=total, status='pending', gateway_response=rzp_order)
                order.payment = payment
                order.save(update_fields=['payment', 'updated_at'])
        except RuntimeError as exc:
            form.add_error(None, str(exc))
        except Exception:
            logger.exception('Checkout creation failed')
            form.add_error(None, 'We could not start the payment. Please try again.')
        else:
            return render(request, 'payment.html', {'payment': payment, 'rzp_order': rzp_order, 'total_amount': total, 'razorpay_key': settings.RAZORPAY_KEY_ID, 'order': order})
    return render(request, 'checkout.html', {'form': form, 'cart_items': cart_items, 'subtotal': subtotal, 'shipping': shipping, 'tax': tax, 'discount': discount, 'total': total})


@login_required
@transaction.atomic
def payment_success(request):
    if request.method != 'POST':
        return redirect('cart:view_cart')
    razorpay_order_id = request.POST.get('razorpay_order_id', '').strip()
    razorpay_payment_id = request.POST.get('razorpay_payment_id', '').strip()
    razorpay_signature = request.POST.get('razorpay_signature', '').strip()
    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        messages.error(request, 'Payment response was incomplete.')
        return redirect('cart:view_cart')
    payment = get_object_or_404(Payment.objects.select_related('order'), order_id=razorpay_order_id, user=request.user)
    if payment.status == 'paid':
        return redirect('order:payment_receipt', payment_id=payment.pk)
    try:
        client = _get_client()
        client.utility.verify_payment_signature({'razorpay_order_id': razorpay_order_id, 'razorpay_payment_id': razorpay_payment_id, 'razorpay_signature': razorpay_signature})
        order = _finalize_paid_payment(payment, razorpay_payment_id, razorpay_signature)
    except ValueError:
        # Payment may be captured while stock changed; try an automatic refund.
        try:
            _get_client().payment.refund(razorpay_payment_id)
            payment.payment_id = payment.payment_id or razorpay_payment_id
            payment.status = 'refunded'
            payment.refund_amount = payment.amount
            payment.refunded_at = timezone.now()
            payment.save(update_fields=['status', 'refund_amount', 'refunded_at', 'payment_id'])
            payment.order.order_status = 'cancelled'
            payment.order.cancellation_reason = 'Automatic refund: inventory was no longer available.'
            payment.order.save(update_fields=['order_status', 'cancellation_reason', 'updated_at'])
            transaction.on_commit(lambda: send_order_event_email(payment.order, 'refunded', 'A payment was refunded automatically because the requested stock was unavailable.'))
            messages.error(request, 'Payment was received but the selected stock was no longer available. The payment was sent for refund.')
        except Exception:
            logger.exception('Automatic refund failed after inventory conflict')
            messages.error(request, 'Payment was received but stock changed. Please contact support for immediate assistance.')
        return redirect('cart:view_cart')
    except Exception:
        logger.exception('Payment verification failed')
        Payment.objects.filter(pk=payment.pk).exclude(status__in=['paid', 'refunded']).update(status='failed')
        messages.error(request, 'Payment verification failed. No order was marked as paid.')
        return redirect('cart:view_cart')
    cart = Cart.objects.filter(user=request.user).first()
    if cart:
        cart.items.all().delete()
    messages.success(request, 'Payment successful — your order is confirmed.')
    return redirect('order:payment_receipt', payment_id=payment.pk)


@csrf_exempt
@transaction.atomic
def razorpay_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'POST required'}, status=405)
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    if not secret:
        return JsonResponse({'detail': 'Webhook secret not configured'}, status=503)
    signature = request.headers.get('X-Razorpay-Signature', '')
    expected = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
    if not signature or not hmac.compare_digest(expected, signature):
        return JsonResponse({'detail': 'Invalid signature'}, status=400)
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'Invalid JSON'}, status=400)
    event = payload.get('event', '')
    entity = (((payload.get('payload') or {}).get('payment') or {}).get('entity') or {})
    order_entity = (((payload.get('payload') or {}).get('order') or {}).get('entity') or {})
    order_id = entity.get('order_id') or order_entity.get('id')
    payment_id = entity.get('id')
    payment = Payment.objects.select_for_update().filter(order_id=order_id).select_related('order').first()
    if not payment and payment_id:
        payment = Payment.objects.select_for_update().filter(payment_id=payment_id).select_related('order').first()
    if payment:
        payment.webhook_event = event
        payment.gateway_response = payload
        payment.gateway_status = entity.get('status', payment.gateway_status)
        payment.save(update_fields=['webhook_event', 'gateway_response', 'gateway_status'])
        if event in {'payment.captured', 'order.paid'} and payment.status != 'paid':
            try:
                _finalize_paid_payment(payment, payment_id=payment_id, gateway_payload=entity)
            except ValueError:
                logger.error('Webhook payment captured but inventory unavailable for %s', payment.order.invoice_number)
                try:
                    _get_client().payment.refund(payment_id)
                    payment.status = 'refunded'
                    payment.refund_amount = payment.amount
                    payment.refunded_at = timezone.now()
                    payment.save(update_fields=['status', 'refund_amount', 'refunded_at'])
                    payment.order.order_status = 'cancelled'
                    payment.order.cancellation_reason = 'Automatic refund: inventory was no longer available.'
                    payment.order.save(update_fields=['order_status', 'cancellation_reason', 'updated_at'])
                except Exception:
                    logger.exception('Automatic webhook refund failed for %s', payment.order.invoice_number)
        elif event == 'payment.failed' and payment.status not in {'paid', 'refunded'}:
            payment.status = 'failed'
            payment.save(update_fields=['status'])
        elif event in {'refund.created', 'refund.processed'} and payment.status != 'refunded':
            refunded_paise = Decimal(str(entity.get('amount_refunded') or (payment.amount * 100)))
            payment.refund_amount = (refunded_paise / 100).quantize(Decimal('0.01'))
            payment.refunded_at = timezone.now()
            if payment.refund_amount >= payment.amount:
                payment.status = 'refunded'
                order = getattr(payment, 'order', None)
                if order and order.order_status not in {'cancelled', 'returned'}:
                    if order.inventory_deducted:
                        for item in order.items.select_related('product'):
                            if item.product_id:
                                product = ImageWithCaption.objects.select_for_update().get(pk=item.product_id)
                                product.stock_quantity += item.quantity
                                product.save(update_fields=['stock_quantity', 'updated_at'])
                        order.inventory_deducted = False
                    order.order_status = 'cancelled'
                    order.cancellation_reason = order.cancellation_reason or 'Payment refunded through Razorpay.'
                    order.save(update_fields=['order_status', 'cancellation_reason', 'inventory_deducted', 'updated_at'])
            payment.save(update_fields=['status', 'refund_amount', 'refunded_at'])
    return JsonResponse({'status': 'ok'})


@login_required
def payment_receipt(request, payment_id):
    payment = get_object_or_404(Payment.objects.select_related('order'), pk=payment_id, user=request.user)
    return render(request, 'payment_receipt.html', {'payment': payment})


@login_required
def customer_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items').select_related('payment')
    return render(request, 'orders.html', {'orders': orders})


@login_required
def order_detail(request, invoice_number):
    order = get_object_or_404(Order.objects.prefetch_related('items').select_related('payment'), invoice_number=invoice_number, user=request.user)
    return render(request, 'order_detail.html', {'order': order})


@login_required
@transaction.atomic
def cancel_order(request, invoice_number):
    order = get_object_or_404(Order.objects.select_for_update().select_related('payment'), invoice_number=invoice_number, user=request.user)
    if request.method != 'POST':
        return redirect('order:order_detail', invoice_number=invoice_number)
    reason = request.POST.get('reason', '').strip() or 'Customer requested cancellation.'
    if order.order_status not in {'payment_pending', 'processing'}:
        messages.warning(request, 'This order can no longer be cancelled online.')
        return redirect('order:order_detail', invoice_number=invoice_number)
    if order.payment and order.payment.status == 'paid':
        try:
            client = _get_client()
            client.payment.refund(order.payment.payment_id)
        except Exception:
            logger.exception('Order refund failed')
            messages.error(request, 'We could not process the refund right now. Please contact support.')
            return redirect('order:order_detail', invoice_number=invoice_number)
        order.payment.status = 'refunded'
        order.payment.refund_amount = order.payment.amount
        order.payment.refunded_at = timezone.now()
        order.payment.save(update_fields=['status', 'refund_amount', 'refunded_at'])
        if order.inventory_deducted:
            for item in order.items.select_related('product'):
                if item.product_id:
                    product = ImageWithCaption.objects.select_for_update().get(pk=item.product_id)
                    product.stock_quantity += item.quantity
                    product.save(update_fields=['stock_quantity', 'updated_at'])
            order.inventory_deducted = False
    order.order_status = 'cancelled'
    order.cancellation_reason = reason
    order.save(update_fields=['order_status', 'cancellation_reason', 'inventory_deducted', 'updated_at'])
    transaction.on_commit(lambda: send_order_event_email(order, 'cancelled', f'Reason: {reason}'))
    if order.payment and order.payment.status == 'refunded':
        transaction.on_commit(lambda: send_order_event_email(order, 'refunded', 'The payment refund has been initiated through Razorpay.'))
    messages.success(request, 'Your cancellation request was processed.')
    return redirect('order:order_detail', invoice_number=invoice_number)


@login_required
def request_return(request, invoice_number):
    order = get_object_or_404(Order, invoice_number=invoice_number, user=request.user)
    if request.method != 'POST':
        return redirect('order:order_detail', invoice_number=invoice_number)
    if order.order_status != 'delivered' or not order.delivered_at or order.delivered_at < timezone.now() - timedelta(days=7):
        messages.warning(request, 'Returns are available for delivered orders within 7 days.')
        return redirect('order:order_detail', invoice_number=invoice_number)
    reason = request.POST.get('reason', '').strip()
    if not reason:
        messages.error(request, 'Please tell us why you are requesting a return.')
        return redirect('order:order_detail', invoice_number=invoice_number)
    order.return_requested = True
    order.return_reason = reason
    order.return_status = 'requested'
    order.order_status = 'return_pending'
    order.save(update_fields=['return_requested', 'return_reason', 'return_status', 'order_status', 'updated_at'])
    transaction.on_commit(lambda: send_order_event_email(order, 'return_pending', f'Reason: {reason}'))
    messages.success(request, 'Your return request has been sent to the Lavkush Furniture team.')
    return redirect('order:order_detail', invoice_number=invoice_number)


@user_passes_test(_admin)
def admin_finance_dashboard(request):
    today = timezone.localdate()
    paid = Payment.objects.filter(status='paid')
    totals = paid.aggregate(total=Sum('amount'))
    daily = paid.filter(created_at__date=today).aggregate(value=Sum('amount'))['value'] or 0
    monthly = paid.filter(created_at__year=today.year, created_at__month=today.month).aggregate(value=Sum('amount'))['value'] or 0
    order_qs = Order.objects.exclude(order_status__in=['cancelled', 'payment_pending'])
    top_products = OrderItem.objects.filter(order__in=order_qs).values('product_name').annotate(units=Sum('quantity'), revenue=Sum(ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField(max_digits=14, decimal_places=2)))).order_by('-units')[:5]
    from django.contrib.auth.models import User
    context = {
        'total': totals.get('total') or 0, 'daily': daily, 'monthly': monthly,
        'failed': Payment.objects.filter(status='failed').count(),
        'refunded': Payment.objects.filter(status='refunded').aggregate(value=Sum('refund_amount'))['value'] or 0,
        'orders_count': order_qs.count(), 'customers_count': order_qs.values('user_id').distinct().count(),
        'new_customers_month': User.objects.filter(date_joined__year=today.year, date_joined__month=today.month).count(),
        'repeat_customers': order_qs.values('user_id').annotate(order_count=Count('id')).filter(order_count__gte=2).count(),
        'avg_order_value': order_qs.aggregate(value=Avg('total_amount'))['value'] or 0,
        'top_products': top_products,
        'payments': Payment.objects.select_related('user').order_by('-created_at')[:20],
        'recent_orders': Order.objects.select_related('user', 'payment').order_by('-created_at')[:12],
    }
    return render(request, 'admin_finance_dashboard.html', context)


def _refund_redirect(request):
    from django.urls import reverse
    return redirect(safe_next_url(request, request.POST.get('next'), reverse('order:admin_finance_dashboard')))


@user_passes_test(_admin)
@transaction.atomic
def refund_payment(request, payment_id):
    if request.method != 'POST':
        return _refund_redirect(request)
    payment = get_object_or_404(Payment.objects.select_for_update().select_related('order'), pk=payment_id)
    if payment.status != 'paid' or not payment.payment_id:
        messages.warning(request, 'Only captured payments can be refunded.')
        return _refund_redirect(request)
    try:
        _get_client().payment.refund(payment.payment_id)
        payment.status = 'refunded'
        payment.refund_amount = payment.amount
        payment.refunded_at = timezone.now()
        payment.save(update_fields=['status', 'refund_amount', 'refunded_at'])
        if payment.order:
            order = payment.order
            if order.inventory_deducted:
                for item in order.items.select_related('product'):
                    if item.product_id:
                        product = ImageWithCaption.objects.select_for_update().get(pk=item.product_id)
                        product.stock_quantity += item.quantity
                        product.save(update_fields=['stock_quantity', 'updated_at'])
                order.inventory_deducted = False
            order.order_status = 'cancelled'
            order.cancellation_reason = 'Refund processed by staff.'
            order.save(update_fields=['order_status', 'cancellation_reason', 'inventory_deducted', 'updated_at'])
            transaction.on_commit(lambda: send_order_event_email(order, 'refunded', f'Refund amount: ₹{payment.refund_amount:.2f}'))
        messages.success(request, f'Refund started for {payment.payment_id}.')
    except Exception:
        logger.exception('Refund failed')
        messages.error(request, 'Refund failed. No local payment status was changed.')
    return _refund_redirect(request)


@login_required
def customer_finance_dashboard(request):
    qs = Payment.objects.filter(user=request.user)
    total = qs.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    now = timezone.localdate()
    monthly = qs.filter(status='paid', created_at__year=now.year, created_at__month=now.month).aggregate(total=Sum('amount'))['total'] or 0
    refunded = qs.filter(status='refunded').aggregate(total=Sum('refund_amount'))['total'] or 0
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    latest_payment = qs.select_related('order').first()
    context = {'total': total, 'monthly': monthly, 'failed': qs.filter(status='failed').count(), 'refunded': refunded, 'payments': qs[:10], 'orders': orders[:8], 'payment': latest_payment}
    return render(request, 'customer_finance_dashboard.html', context)


@login_required
def download_receipt_pdf(request, payment_id):
    payment = get_object_or_404(Payment.objects.select_related('order'), pk=payment_id, user=request.user)
    order = get_object_or_404(Order.objects.prefetch_related('items'), payment=payment)
    if payment.status not in {'paid', 'refunded'}:
        messages.warning(request, 'A receipt is available only after a payment is completed.')
        return redirect('order:customer_orders')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{order.invoice_number}.pdf"'
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title = ParagraphStyle('LFTitle', parent=styles['Title'], alignment=TA_CENTER, spaceAfter=16)
    elements = [Paragraph('Lavkush Furniture', title), Paragraph(f'Invoice: {order.invoice_number}', styles['Normal']), Paragraph(f'Date: {order.created_at:%d %b %Y, %I:%M %p}', styles['Normal']), Spacer(1, 12)]
    ship_to = xml_escape(f'{order.first_name} {order.last_name}, {order.shipping_address}, {order.address_line2}, {order.city}, {order.state} - {order.postal_code}, {order.country}'.replace(', ,', ','))
    elements.append(Paragraph(f'<b>Ship to:</b> {ship_to}', styles['BodyText']))
    elements.append(Spacer(1, 14))
    data = [['Product', 'Qty', 'Price', 'Total']]
    for item in order.items.all():
        data.append([Paragraph(xml_escape(item.product_name), styles['BodyText']), str(item.quantity), f'Rs. {item.price:.2f}', f'Rs. {item.subtotal:.2f}'])
    data.append(['', '', 'Subtotal', f'Rs. {order.subtotal:.2f}'])
    if order.discount_amount:
        data.append(['', '', 'Discount', f'- Rs. {order.discount_amount:.2f}'])
    if order.shipping_amount:
        data.append(['', '', 'Shipping', f'Rs. {order.shipping_amount:.2f}'])
    if order.tax_amount:
        data.append(['', '', 'GST', f'Rs. {order.tax_amount:.2f}'])
    data.append(['', '', 'Grand Total', f'Rs. {order.total_amount:.2f}'])
    table = Table(data, colWidths=[3.0 * inch, .6 * inch, 1.0 * inch, 1.2 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#243244')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), .5, colors.HexColor('#cbd5e1')), ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements += [table, Spacer(1, 14), Paragraph('Thank you for choosing Lavkush Furniture.', styles['BodyText'])]
    doc.build(elements)
    return response
