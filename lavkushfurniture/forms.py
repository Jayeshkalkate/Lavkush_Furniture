from django import forms
from django.contrib.auth.models import User
from account.models import Items  # Import the profile model


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Items  # Use the Items model for user profile
        fields = ['phone_number', 'address', 'city']  # Adjust to match Items fields
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }