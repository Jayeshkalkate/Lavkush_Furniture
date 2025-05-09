from django import forms
from .models import ImageWithCaption

class ImageForm(forms.ModelForm):
    class Meta:
        model = ImageWithCaption
        fields = ['caption', 'price', 'description', 'dimensions', 'materials', 'image']  # Removed 'uploaded_at'

SORT_CHOICES = [
    ('price_asc', 'Price: Low to High'),
    ('price_desc', 'Price: High to Low'),
    ('latest', 'Latest'),
    ('oldest', 'Oldest'),
    ('rating', 'Highest Rated'),
]

class FilterForm(forms.Form):
    keyword = forms.CharField(required=False, label='Search')
    min_price = forms.DecimalField(required=False, decimal_places=2, label='Min Price')
    max_price = forms.DecimalField(required=False, decimal_places=2, label='Max Price')
    materials = forms.CharField(required=False, label='Material')
    sort_by = forms.ChoiceField(choices=SORT_CHOICES, required=False)
