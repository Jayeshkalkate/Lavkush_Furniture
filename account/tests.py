from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Items

User = get_user_model()

class AccountTests(TestCase):
    def test_register_persists_profile_details(self):
        response = self.client.post(reverse('register'), {
            'full_name': 'Asha Patil', 'email': 'asha@example.com', 'phone_number': '9876543210',
            'address': 'Shivaji Nagar', 'city': 'Nandurbar', 'username': 'asha',
            'password': 'StrongPass123!', 'confirm_password': 'StrongPass123!',
        })
        self.assertRedirects(response, reverse('homepage'))
        user = User.objects.get(username='asha')
        profile = Items.objects.get(user=user)
        self.assertEqual(profile.city, 'Nandurbar')
        self.assertEqual(user.first_name, 'Asha')
        self.assertEqual(user.last_name, 'Patil')

    def test_logout_requires_post(self):
        user = User.objects.create_user(username='buyer', password='StrongPass123!')
        self.client.force_login(user)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        self.assertTrue('_auth_user_id' in self.client.session)


class LoginSafetyTests(TestCase):
    def setUp(self):
        User.objects.create_user(username='buyer', password='StrongPass123!')

    def test_login_ignores_external_next_url(self):
        response = self.client.post(reverse('login') + '?next=https://evil.example.com/', {'username': 'buyer', 'password': 'StrongPass123!'})
        self.assertRedirects(response, reverse('homepage'))

    def test_login_honours_internal_next_url(self):
        response = self.client.post(reverse('login') + '?next=/cart/', {'username': 'buyer', 'password': 'StrongPass123!'})
        self.assertRedirects(response, '/cart/', fetch_redirect_response=False)

    def test_wrong_password_shows_error(self):
        response = self.client.post(reverse('login'), {'username': 'buyer', 'password': 'nope'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password.')

    def test_user_with_orders_is_deactivated_not_deleted(self):
        from order.models import Order
        admin = User.objects.create_superuser(username='boss', email='boss@example.com', password='StrongPass123!')
        buyer = User.objects.get(username='buyer')
        Order.objects.create(user=buyer, total_amount=100, subtotal=100, first_name='B', shipping_address='A', city='C', state='S', postal_code='425412', phone='9876543210', email='b@example.com')
        self.client.force_login(admin)
        self.client.post(reverse('delete_user', args=[buyer.pk]))
        buyer.refresh_from_db()
        self.assertFalse(buyer.is_active)
