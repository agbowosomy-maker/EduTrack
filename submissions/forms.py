from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError

from .models import Submission


class SubmissionForm(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ['content', 'file']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 8,
                'placeholder': 'Write your assignment answer here...',
            }),
        }

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        uploaded_file = self.files.get('file')

        # On an update, an existing file may already be attached.
        existing_file = (
            self.instance.file
            if self.instance and self.instance.pk
            else None
        )

        if not content and not uploaded_file and not existing_file:
            raise ValidationError(
                'Provide written work or upload a file before submitting.'
            )

        return content

    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file')

        if not uploaded_file:
            return uploaded_file

        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt'}
        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in allowed_extensions:
            raise ValidationError(
                'Only PDF, DOC, DOCX and TXT files are allowed.'
            )

        max_size = 5 * 1024 * 1024  # 5 MB

        if uploaded_file.size > max_size:
            raise ValidationError(
                'The uploaded file must not exceed 5 MB.'
            )

        return uploaded_file


class GradingForm(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ['status', 'grade', 'feedback']

        widgets = {
            'status': forms.Select(),
            'grade': forms.NumberInput(attrs={
                'min': 0,
                'max': 100,
                'step': '0.01',
                'placeholder': 'Enter grade out of 100',
            }),
            'feedback': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Provide feedback to the student...',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        status = cleaned_data.get('status')
        grade = cleaned_data.get('grade')
        feedback = cleaned_data.get('feedback', '').strip()

        if status == Submission.Status.REVIEWED and grade is None:
            self.add_error(
                'grade',
                'A grade is required when marking work as reviewed.'
            )

        if status == Submission.Status.REVISION_REQUIRED and not feedback:
            self.add_error(
                'feedback',
                'Feedback is required when requesting a revision.'
            )

        if grade is not None and not 0 <= grade <= 100:
            self.add_error(
                'grade',
                'The grade must be between 0 and 100.'
            )

        return cleaned_data