from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import Order, Payment, OrderItem

User = get_user_model()

class OrderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='StrongPass123!')

    def test_order_generates_invoice_number(self):
        order = Order.objects.create(user=self.user, total_amount=Decimal('1000'), subtotal=Decimal('1000'), first_name='Buyer', shipping_address='Address', city='Nandurbar', state='Maharashtra', postal_code='425412', phone='9876543210', email='buyer@example.com')
        self.assertTrue(order.invoice_number.startswith('LF-'))

    def test_order_item_subtotal_is_price_times_quantity(self):
        order = Order.objects.create(user=self.user, total_amount=Decimal('3000'), subtotal=Decimal('3000'), first_name='Buyer', shipping_address='Address', city='Nandurbar', state='Maharashtra', postal_code='425412', phone='9876543210', email='buyer@example.com')
        item = OrderItem.objects.create(order=order, product_name='Table', price=Decimal('1500'), quantity=2)
        self.assertEqual(item.subtotal, Decimal('3000'))
