from django.db import models
from cloudinary.models import CloudinaryField  # Import CloudinaryField

class ImageWithCaption(models.Model):
    image = CloudinaryField('image')  # Cloudinary image
    caption = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # New price field
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.caption} - ₹{self.price if self.price else 'N/A'}"
