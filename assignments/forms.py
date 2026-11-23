
from django import forms
from django.utils import timezone

from .models import Assignment
from subjects.models import Subject


class AssignmentForm(forms.ModelForm):

    class Meta:
        model = Assignment
        fields = [
            'title',
            'description',
            'subject',
            'due_date',
            'is_published',
        ]

        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter assignment title',
                'class': 'form-control',
            }),

            'description': forms.Textarea(attrs={
                'placeholder': 'Enter assignment instructions',
                'rows': 6,
                'class': 'form-control',
            }),

            'subject': forms.Select(attrs={
                'class': 'form-control',
            }),

            'due_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                },
                format='%Y-%m-%dT%H:%M',
            ),

            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
            }),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)

        super().__init__(*args, **kwargs)

        self.fields['due_date'].input_formats = [
            '%Y-%m-%dT%H:%M',
        ]

        if teacher is not None:
            self.fields['subject'].queryset = Subject.objects.filter(
                teacher=teacher
            )

    def clean_title(self):
        title = self.cleaned_data['title'].strip()

        if not title:
            raise forms.ValidationError(
                'Assignment title cannot be empty.'
            )

        return title

    def clean_due_date(self):
        due_date = self.cleaned_data['due_date']

        if due_date <= timezone.now():
            raise forms.ValidationError(
                'The assignment deadline must be in the future.'
            )

        return due_date
