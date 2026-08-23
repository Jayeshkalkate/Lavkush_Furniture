from django import forms
from .models import TeamMember


class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ['name', 'role', 'bio', 'image', 'is_visible']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name').strip()
        if not name:
            raise forms.ValidationError("Name is required.")
        return name