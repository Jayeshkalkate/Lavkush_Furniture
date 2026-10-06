from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Category, ImageWithCaption, Rating

User = get_user_model()

class CatalogTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='StrongPass123!')
        self.category = Category.objects.create(name='Sofas & Seating', slug='sofas-seating')
        self.product = ImageWithCaption.objects.create(caption='Test Sofa', price=Decimal('25000.00'), category=self.category, stock_quantity=5, is_active=True)

    def test_product_get_absolute_url_is_slug_based(self):
        self.assertEqual(self.product.get_absolute_url(), reverse('furniture_detail', kwargs={'slug': self.product.slug}))
        self.assertEqual(self.product.sku, f'LF-{self.product.pk:05d}')

    def test_gallery_search_finds_product(self):
        response = self.client.get(reverse('gallery'), {'keyword': 'Test Sofa'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Sofa')

    def test_review_is_unique_and_writable(self):
        Rating.objects.create(user=self.user, item=self.product, rating=5, title='Great', review_text='Comfortable and solid.')
        response = self.client.get(self.product.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Comfortable and solid.')


class HealthAndPagesTests(TestCase):
    def test_health_endpoint(self):
        response = self.client.get(reverse('healthz'))
        self.assertEqual(response.status_code, 200)

    def test_public_pages_render(self):
        for name in ['homepage', 'aboutus', 'services', 'contactus', 'gallery', 'our_team', 'privacy_policy', 'terms', 'login', 'register', 'robots_txt']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
