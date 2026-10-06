from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from gallery.models import Category, ImageWithCaption
from order.models import Order


class DashboardAccessTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='owner', password='StrongPass123!', is_staff=True)
        self.customer = User.objects.create_user(username='buyer', password='StrongPass123!')

    def test_anonymous_and_customers_are_sent_to_login(self):
        for user in (None, self.customer):
            if user:
                self.client.force_login(user)
            response = self.client.get(reverse('dashboard:home'))
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse('login'), response['Location'])

    def test_staff_can_open_every_page(self):
        self.client.force_login(self.staff)
        for name in ['home', 'products', 'product_add', 'bulk_upload', 'categories', 'category_add', 'orders',
                     'payments', 'customers', 'coupons', 'coupon_add', 'reviews', 'team']:
            self.assertEqual(self.client.get(reverse(f'dashboard:{name}')).status_code, 200, name)

    def test_staff_login_lands_on_dashboard(self):
        response = self.client.post(reverse('login'), {'username': 'owner', 'password': 'StrongPass123!'})
        self.assertRedirects(response, reverse('dashboard:home'), fetch_redirect_response=False)


class DashboardActionTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='owner', password='StrongPass123!', is_staff=True)
        self.client.force_login(self.staff)
        self.product = ImageWithCaption.objects.create(caption='Teak Door', price=10000, stock_quantity=5, is_active=True)

    def test_quick_update_price_and_stock(self):
        self.client.post(reverse('dashboard:product_quick', args=[self.product.pk]), {'price': '12,500', 'stock_quantity': '8'})
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, Decimal('12500'))
        self.assertEqual(self.product.stock_quantity, 8)

    def test_quick_update_rejects_negative_stock(self):
        self.client.post(reverse('dashboard:product_quick', args=[self.product.pk]), {'price': '100', 'stock_quantity': '-1'})
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 5)

    def test_toggle_visibility(self):
        self.client.post(reverse('dashboard:product_toggle', args=[self.product.pk]), {'field': 'is_active'})
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)

    def test_only_superuser_can_delete_product(self):
        self.client.post(reverse('dashboard:product_delete', args=[self.product.pk]))
        self.assertTrue(ImageWithCaption.objects.filter(pk=self.product.pk).exists())

    def test_category_created_with_slug(self):
        self.client.post(reverse('dashboard:category_add'), {'name': 'Wardrobes', 'description': 'x', 'is_active': 'on'})
        self.assertEqual(Category.objects.get(name='Wardrobes').slug, 'wardrobes')

    def test_order_status_update_sets_shipped_time(self):
        order = Order.objects.create(user=self.staff, total_amount=100, subtotal=100, first_name='A', shipping_address='x', city='c',
                                     state='s', postal_code='425412', phone='9876543210', email='a@example.com', order_status='processing')
        self.client.post(reverse('dashboard:order_detail', args=[order.invoice_number]),
                         {'order_status': 'shipped', 'shipping_provider': 'VRL', 'tracking_number': 'LR123', 'expected_delivery': '', 'return_status': 'none'})
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'shipped')
        self.assertIsNotNone(order.shipped_at)
