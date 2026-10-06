from django import forms

from gallery.forms import ImageForm
from gallery.models import Category
from order.models import Coupon, Order


def style_fields(form):
    """Give every widget the right Bootstrap class."""
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs['class'] = 'form-check-input'
        elif isinstance(widget, forms.Select):
            widget.attrs['class'] = 'form-select'
        elif isinstance(widget, forms.RadioSelect):
            continue
        else:
            widget.attrs['class'] = 'form-control'


class DashboardProductForm(ImageForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['caption'].label = 'Product name'
        self.fields['price'].label = 'Price (₹)'
        self.fields['image'].label = 'Main photo'
        self.fields['is_active'].label = 'Visible on website'
        self.fields['is_featured'].label = 'Show on homepage (featured)'

    def clean_stock_quantity(self):
        qty = self.cleaned_data.get('stock_quantity')
        if qty is None or qty < 0:
            raise forms.ValidationError('Stock cannot be negative.')
        return qty


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'is_active']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['is_active'].label = 'Visible on website'


class OrderUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_status', 'shipping_provider', 'tracking_number', 'expected_delivery', 'return_status']
        widgets = {'expected_delivery': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['order_status'].label = 'Order status'
        self.fields['shipping_provider'].label = 'Courier / transport'
        self.fields['tracking_number'].label = 'Tracking / LR number'
        self.fields['expected_delivery'].label = 'Expected delivery date'
        self.fields['return_status'].label = 'Return status'


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_type', 'value', 'minimum_order_value', 'usage_limit', 'valid_from', 'valid_until', 'active']
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'valid_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['value'].label = 'Discount value (% or ₹)'
        self.fields['minimum_order_value'].label = 'Minimum order value (₹)'
        self.fields['active'].label = 'Coupon is active'

    def clean_code(self):
        return (self.cleaned_data.get('code') or '').strip().upper()

    def clean(self):
        data = super().clean()
        value = data.get('value')
        if value is not None:
            if value <= 0:
                self.add_error('value', 'Discount must be greater than zero.')
            elif data.get('discount_type') == 'percent' and value > 100:
                self.add_error('value', 'A percentage discount cannot exceed 100.')
        start, end = data.get('valid_from'), data.get('valid_until')
        if start and end and end <= start:
            self.add_error('valid_until', 'End date must be after the start date.')
        return data


class BulkUploadForm(forms.Form):
    file = forms.FileField(label='CSV or Excel file', widget=forms.ClearableFileInput(attrs={'accept': '.csv,.xlsx', 'class': 'form-control'}))
