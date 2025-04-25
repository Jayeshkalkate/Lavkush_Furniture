from django.db import models
from cloudinary.models import CloudinaryField  # Import CloudinaryField
from django.contrib.auth.models import User

def furniture_detail(request, pk):
    item = get_object_or_404(ImageWithCaption, pk=pk)
    return render(request, 'furniture_detail.html', {'item': item})

class ImageWithCaption(models.Model):
    image = CloudinaryField('image')  # Cloudinary image
    caption = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # New price field
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True, null=True)
    materials = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.caption} - ₹{self.price if self.price else 'N/A'}"

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(ImageWithCaption, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=1, choices=[(i, i) for i in range(1, 6)])  # Rating between 1 and 5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'item']  # Ensure each user can only rate an item once

    def __str__(self):
        return f"{self.user.username} rated {self.item.caption} {self.rating} stars"
