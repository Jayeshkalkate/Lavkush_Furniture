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
