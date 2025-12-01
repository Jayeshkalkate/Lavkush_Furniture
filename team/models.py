from django.db import models
from cloudinary.models import CloudinaryField

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=200)
    bio = models.TextField()
    image = CloudinaryField('image')
    # is_visible = models.BooleanField(default=True)

    def __str__(self):
        return self.name
