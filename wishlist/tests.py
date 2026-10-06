from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from gallery.models import ImageWithCaption
from .models import Wishlist

User = get_user_model()

class WishlistTests(TestCase):
    def test_clear_wishlist_is_post_only(self):
        user = User.objects.create_user(username='buyer', password='StrongPass123!')
        product = ImageWithCaption.objects.create(caption='Wish Sofa', price=15000, stock_quantity=2, is_active=True)
        Wishlist.objects.create(user=user, item=product)
        self.client.force_login(user)
        self.client.post(reverse('wishlist:clear_wishlist'))
        self.assertFalse(Wishlist.objects.filter(user=user).exists())
