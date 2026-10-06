from decimal import Decimal
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Cart, CartItem
from gallery.models import ImageWithCaption
from lavkushfurniture.utils import safe_next_url

logger = logging.getLogger(__name__)
SESSION_KEY = 'guest_cart'


def _guest_rows(request):
    raw = request.session.get(SESSION_KEY, {})
    product_ids = [int(pid) for pid in raw.keys() if str(pid).isdigit()]
    products = {p.id: p for p in ImageWithCaption.objects.filter(id__in=product_ids, is_active=True)}
    rows = []
    clean = {}
    for pid_str, qty in raw.items():
        if not str(pid_str).isdigit():
            continue
        product = products.get(int(pid_str))
        if not product or product.price is None or product.stock_quantity <= 0:
            continue
        try:
            quantity = max(1, min(int(qty), product.stock_quantity))
        except (TypeError, ValueError):
            quantity = 1
        clean[str(product.id)] = quantity
        rows.append({'product': product, 'quantity': quantity, 'subtotal': product.price * quantity})
    request.session[SESSION_KEY] = clean
    return rows


def merge_guest_cart(request, user):
    raw = request.session.pop(SESSION_KEY, {})
    if not raw:
        return
    cart, _ = Cart.objects.get_or_create(user=user)
    for pid_str, qty in raw.items():
        try:
            product = ImageWithCaption.objects.get(pk=int(pid_str), is_active=True)
            if product.stock_quantity <= 0:
                continue
            quantity = max(1, min(int(qty), product.stock_quantity))
            item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity})
            if not created:
                item.quantity = min(item.quantity + quantity, product.stock_quantity)
                item.save(update_fields=['quantity'])
        except (ImageWithCaption.DoesNotExist, ValueError):
            continue


def view_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.select_related('product').all()
        total_price = sum((item.subtotal for item in items), Decimal('0.00'))
        return render(request, 'view_cart.html', {'items': items, 'total_price': total_price, 'is_guest': False})
    rows = _guest_rows(request)
    total_price = sum((row['subtotal'] for row in rows), Decimal('0.00'))
    return render(request, 'view_cart.html', {'items': rows, 'total_price': total_price, 'is_guest': True})


def add_to_cart(request, product_id):
    if request.method != 'POST':
        return redirect('gallery')
    product = get_object_or_404(ImageWithCaption, pk=product_id, is_active=True)
    if product.stock_quantity <= 0:
        messages.warning(request, f"'{product.caption}' is currently out of stock.")
        return redirect(product.get_absolute_url())
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 1})
        if not created:
            item.quantity = min(item.quantity + 1, product.stock_quantity)
            item.save(update_fields=['quantity'])
        messages.success(request, f"'{product.caption}' was added to your cart.")
    else:
        guest = request.session.setdefault(SESSION_KEY, {})
        current = int(guest.get(str(product.id), 0))
        guest[str(product.id)] = min(current + 1, product.stock_quantity)
        request.session.modified = True
        messages.success(request, f"'{product.caption}' was added to your cart. Sign in at checkout to place the order.")
    return redirect(safe_next_url(request, request.POST.get('next'), reverse('cart:view_cart')))


def remove_from_cart(request, item_id):
    if request.method != 'POST':
        return redirect('cart:view_cart')
    if request.user.is_authenticated:
        item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
        name = item.product.caption
        item.delete()
        messages.success(request, f"Removed '{name}' from your cart.")
    else:
        guest = request.session.get(SESSION_KEY, {})
        guest.pop(str(item_id), None)
        request.session[SESSION_KEY] = guest
        messages.success(request, 'Item removed from your cart.')
    return redirect('cart:view_cart')


@login_required
def update_quantity(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            quantity = 1
        if quantity <= 0:
            item.delete()
            messages.info(request, f"Removed '{item.product.caption}' from your cart.")
        else:
            quantity = min(quantity, item.product.stock_quantity)
            item.quantity = quantity
            item.save(update_fields=['quantity'])
            messages.success(request, 'Cart quantity updated.')
    return redirect('cart:view_cart')


@login_required
def clear_cart(request):
    if request.method == 'POST':
        CartItem.objects.filter(cart__user=request.user).delete()
        messages.success(request, 'Your cart is now empty.')
    return redirect('cart:view_cart')
