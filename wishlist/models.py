from django.db import models
from django.contrib.auth.models import User
from gallery.models import ImageWithCaption

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(ImageWithCaption, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'item')  # Prevent duplicates

    def __str__(self):
        return f"{self.user.username} - {self.item.caption}"
