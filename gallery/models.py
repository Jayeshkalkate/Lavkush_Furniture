from django.db import models
from cloudinary.models import CloudinaryField
from django.contrib.auth.models import User


class ImageWithCaption(models.Model):
    image = CloudinaryField('image')
    caption = models.CharField(max_length=255, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True, null=True)
    materials = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    class Meta:
        ordering = ['-uploaded_at']  # newest first

    def __str__(self):
        return f"{self.caption} - ₹{self.price if self.price else 'N/A'}"

    def get_avg_rating(self):
        return self.ratings.aggregate(avg=models.Avg('rating'))['avg'] or 0


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    item = models.ForeignKey(ImageWithCaption, on_delete=models.CASCADE, related_name='ratings', db_index=True)
    rating = models.PositiveIntegerField(default=1, choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'item']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} rated {self.item.caption} {self.rating} stars"