from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from gallery.models import ImageWithCaption
from .models import Cart, CartItem

User = get_user_model()

class CartTests(TestCase):
    def setUp(self):
        self.product = ImageWithCaption.objects.create(caption='Cart Sofa', price=12000, stock_quantity=3, is_active=True)

    def test_guest_can_add_to_session_cart(self):
        response = self.client.post(reverse('cart:add_to_cart', args=[self.product.pk]), {'next': reverse('cart:view_cart')})
        self.assertRedirects(response, reverse('cart:view_cart'))
        self.assertEqual(self.client.session['guest_cart'][str(self.product.pk)], 1)

    def test_authenticated_cart_quantity_is_capped_by_stock(self):
        user = User.objects.create_user(username='buyer', password='StrongPass123!')
        self.client.force_login(user)
        self.client.post(reverse('cart:add_to_cart', args=[self.product.pk]), {'next': reverse('cart:view_cart')})
        for _ in range(8):
            self.client.post(reverse('cart:add_to_cart', args=[self.product.pk]), {'next': reverse('cart:view_cart')})
        item = CartItem.objects.get(cart__user=user, product=self.product)
        self.assertEqual(item.quantity, 3)


class RedirectSafetyTests(TestCase):
    def test_add_to_cart_ignores_external_next_url(self):
        product = ImageWithCaption.objects.create(caption='Safe Sofa', price=9000, stock_quantity=2, is_active=True)
        response = self.client.post(reverse('cart:add_to_cart', args=[product.pk]), {'next': 'https://evil.example.com/'})
        self.assertRedirects(response, reverse('cart:view_cart'))
