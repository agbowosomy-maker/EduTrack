from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class Assignment(models.Model):

    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.PROTECT,
        related_name='assignments'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_assignments'
    )
    due_date = models.DateTimeField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date']

    def clean(self):
        super().clean()
        if self.subject_id and self.created_by_id:
            if self.subject.teacher_id != self.created_by_id:
                raise ValidationError({
                    'subject': 'The selected subject must belong to the assignment creator'
                })
            if self.created_by.role != self.created_by.Role.TEACHER:
                raise ValidationError({
                    'created_by': 'Only teachers can create assignments'
                })
            if self.due_date and self.due_date <= timezone.now():
                raise ValidationError({
                    'due_date': 'The due date must be in the future'
                })

    def __str__(self):
        return self.title