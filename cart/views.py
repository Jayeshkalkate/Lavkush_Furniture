from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart, CartItem
from gallery.models import ImageWithCaption
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem
import razorpay
from django.conf import settings
from django.shortcuts import render
from .models import Cart

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    return render(
        request, "view_cart.html", {"items": cart_items, "total_price": total_price}
    )


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(ImageWithCaption, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart:view_cart')

@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    return redirect('cart:view_cart')

@login_required
def update_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            item.quantity = quantity
            item.save()
        else:
            item.delete()
    return redirect('cart:view_cart')


@login_required
def create_payment(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    total_amount = sum(item.product.price * item.quantity for item in cart_items)

    if total_amount == 0:
        return redirect("cart:view_cart")

    amount_in_paise = int(total_amount * 100)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    payment = client.order.create(
        {"amount": amount_in_paise, "currency": "INR", "payment_capture": "1"}
    )

    return render(
        request,
        "payment.html",
        {
            "payment": payment,
            "total_amount": total_amount,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
        },
    )
