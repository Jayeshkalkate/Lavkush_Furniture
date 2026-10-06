from django import forms
from django.contrib.auth.models import User
from account.models import Items


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Items
        fields = ['phone_number', 'address', 'city']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'tel'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'autocomplete': 'street-address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'address-level2'}),
        }
