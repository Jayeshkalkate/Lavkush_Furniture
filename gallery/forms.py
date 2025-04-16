from django import forms
from .models import ImageWithCaption

class ImageForm(forms.ModelForm):
    class Meta:
        model = ImageWithCaption
        fields = ['image', 'caption']
