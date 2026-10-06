from django.conf import settings
from cart.models import Cart
from wishlist.models import Wishlist


def site_context(request):
    cart_count = 0
    wishlist_count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).prefetch_related('items').first()
        if cart:
            cart_count = sum(item.quantity for item in cart.items.all())
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
    else:
        guest_cart = request.session.get('guest_cart', {})
        cart_count = sum(int(v) for v in guest_cart.values()) if guest_cart else 0
    return {
        'site_url': settings.SITE_URL,
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
        'support_phone': '+91 84829 98343',
        'support_email': 'lavkushfurniture@gmail.com',
        'business_address': 'Shivaji Nagar, Behind Bus Stand, Nandurbar, Maharashtra 425412',
    }
