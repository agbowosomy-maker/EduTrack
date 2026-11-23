from django.db import models
from django.conf import settings
from django.core.validators import (MinValueValidator, MaxValueValidator)

# Create your models here.
class Submission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED='SUBMITTED', 'Submitted'
        REVIEWED='REVIEWED', 'Reviewed'
        REVISION_REQUIRED='REVISION_REQUIRED', 'Revision Required'

    
    assignment = models.ForeignKey('assignments.Assignment', on_delete=models.PROTECT, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='submissions')
    content = models.TextField(blank=True)
    file = models.FileField(upload_to='submissions/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    grade = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    feedback = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering=['-submitted_at']
        constraints=[models.UniqueConstraint(fields=['assignment', 'student'],
                                             name='unique_student_assignment_submission')]

    def clean(self):
        super().clean()
        if self.student_id:
            if self.student.role != self.student.Role.STUDENT:
                from django.core.exceptions import ValidationError
                raise ValidationError({'student': 'Only students can submit assignments'})

        if self.status == self.Status.REVIEWED and self.grade is None:
            from django.core.exceptions import ValidationError
            raise ValidationError({'grade': 'A grade is required when a submission is reviewed'})

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"