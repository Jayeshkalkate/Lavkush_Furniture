from decimal import Decimal
from django import forms
from .models import ImageWithCaption, Rating


SORT_CHOICES = [
    ('relevance', 'Relevance'),
    ('price_asc', 'Price: Low to High'),
    ('price_desc', 'Price: High to Low'),
    ('latest', 'Newest First'),
    ('rating', 'Highest Rated'),
]


class BulkProductUploadForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'accept': '.csv,.xlsx'}))


class ImageForm(forms.ModelForm):
    class Meta:
        model = ImageWithCaption
        fields = ['caption', 'price', 'description', 'dimensions', 'materials', 'category', 'color', 'stock_quantity', 'is_active', 'is_featured', 'warranty', 'lead_time', 'care_instructions', 'meta_title', 'meta_description', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'care_instructions': forms.Textarea(attrs={'rows': 3}),
            'meta_description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None or price < Decimal('0'):
            raise forms.ValidationError('Enter a valid non-negative price.')
        return price


class FilterForm(forms.Form):
    keyword = forms.CharField(required=False, label='Search products')
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)
    materials = forms.CharField(required=False)
    category = forms.ModelChoiceField(queryset=None, required=False, empty_label='All categories')
    sort_by = forms.ChoiceField(choices=SORT_CHOICES, required=False, initial='relevance')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Category
        self.fields['category'].queryset = Category.objects.filter(is_active=True)


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating', 'title', 'review_text']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            'title': forms.TextInput(attrs={'placeholder': 'What stood out about this product?'}),
            'review_text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your experience with the product.'}),
        }
