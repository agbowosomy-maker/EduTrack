from django.contrib import admin
from .models import Subject

# Register your models here.
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'teacher',
        'created_at',
    )

    list_filter = ('teacher', 'created_at')

    search_fields = (
        'name',
        'description',
        'teacher__username',
    )

    filter_horizontal = ('students',)
