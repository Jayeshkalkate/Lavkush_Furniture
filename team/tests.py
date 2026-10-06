from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import TeamMember

User = get_user_model()

class TeamTests(TestCase):
    def test_team_delete_is_post_only(self):
        admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='StrongPass123!')
        member = TeamMember.objects.create(name='Test Member', role='Designer', bio='Test', image='team/test.jpg', is_visible=True)
        self.client.force_login(admin)
        response = self.client.get(reverse('delete_team_member', args=[member.pk]))
        self.assertRedirects(response, reverse('our_team'))
        self.assertTrue(TeamMember.objects.filter(pk=member.pk).exists())
