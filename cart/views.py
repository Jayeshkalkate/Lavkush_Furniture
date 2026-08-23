import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cart, CartItem
from gallery.models import ImageWithCaption

logger = logging.getLogger(__name__)


@login_required
def view_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product').all()  # prefetch product details
    total_price = cart.total_amount
    return render(request, "view_cart.html", {
        "items": items,
        "total_price": total_price,
    })


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(ImageWithCaption, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.info(request, f"Increased quantity of '{product.caption}' to {cart_item.quantity}.")
    else:
        messages.success(request, f"Added '{product.caption}' to your cart.")

    logger.info(f"User {request.user.username} added product {product.id} to cart.")
    return redirect("cart:view_cart")


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = item.product.caption
    item.delete()
    messages.success(request, f"Removed '{product_name}' from your cart.")
    logger.info(f"User {request.user.username} removed cart item {item_id}.")
    return redirect("cart:view_cart")


@login_required
def update_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
        except ValueError:
            messages.error(request, "Invalid quantity.")
            return redirect("cart:view_cart")

        if quantity > 0:
            item.quantity = quantity
            item.save()
            messages.success(request, f"Updated quantity to {quantity} for '{item.product.caption}'.")
        else:
            item.delete()
            messages.info(request, f"Removed '{item.product.caption}' from your cart (quantity zero).")

        logger.info(f"User {request.user.username} updated cart item {item_id} to {quantity}.")

    return redirect("cart:view_cart")