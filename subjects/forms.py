
from django import forms
from .models import Subject


class SubjectForm(forms.ModelForm):

    class Meta:
        model = Subject
        fields = ['name', 'description']

        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter subject name',
                'class': 'form-control',
            }),

            'description': forms.Textarea(attrs={
                'placeholder': 'Describe what this subject covers',
                'rows': 5,
                'class': 'form-control',
            }),
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()

        if not name:
            raise forms.ValidationError(
                'Subject name cannot be empty.'
            )

        return name
