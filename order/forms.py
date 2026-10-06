from django import forms
from django.utils import timezone
from .models import Coupon, Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'company', 'shipping_address', 'address_line2', 'city', 'state', 'postal_code', 'country', 'phone', 'email', 'order_notes', 'coupon_code']
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3, 'autocomplete': 'street-address'}),
            'order_notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Gate, delivery or customization notes (optional).'}),
            'phone': forms.TextInput(attrs={'autocomplete': 'tel'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'postal_code': forms.TextInput(attrs={'autocomplete': 'postal-code'}),
            'country': forms.TextInput(attrs={'autocomplete': 'country-name'}),
            'coupon_code': forms.TextInput(attrs={'placeholder': 'Coupon code (optional)', 'autocomplete': 'off', 'class': 'form-control'}),
        }

    def clean_postal_code(self):
        value = self.cleaned_data['postal_code'].strip()
        if not value.isalnum() or len(value) < 4:
            raise forms.ValidationError('Enter a valid postal code.')
        return value

    def clean_coupon_code(self):
        value = self.cleaned_data.get('coupon_code', '').strip().upper()
        if not value:
            return ''
        coupon = Coupon.objects.filter(code=value).first()
        if not coupon:
            raise forms.ValidationError('That coupon code is not available.')
        self.coupon = coupon
        return value
