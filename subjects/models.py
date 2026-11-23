from django.db import models
from django.conf import settings

# Create your models here.
class Subject(models.Model):
    name=models.CharField(max_length=150)
    description=models.TextField(blank=True)
    teacher=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='subjects_taught')
    students=models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='enrolled_subjects')
    created_at=models.DateField(auto_now_add=True)

class Meta:
    ordering=['name']
    constraints=[models.UniqueConstraint(fields=['teacher', 'name'], 
                                         name='unique_subject_per_teacher')]

def __str__(self):
    return self.name
