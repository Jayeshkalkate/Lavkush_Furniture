from django.db import models
from cloudinary.models import CloudinaryField  # Import CloudinaryField

class ImageWithCaption(models.Model):
    image = CloudinaryField('image')  # Replace ImageField with CloudinaryField
    caption = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.caption
