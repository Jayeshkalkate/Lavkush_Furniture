from django import forms
from .models import ImageWithCaption

class ImageForm(forms.ModelForm):
    class Meta:
        model = ImageWithCaption
        fields = ['caption', 'price', 'description', 'dimensions', 'materials', 'image']  # Removed 'uploaded_at'
