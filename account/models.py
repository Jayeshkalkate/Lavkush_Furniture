from django.db import models
from django.contrib.auth.models import User


class Items(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='items')
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = 'Items'

    def __str__(self):
        return f"{self.user.username}'s profile"