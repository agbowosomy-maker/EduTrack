
from django.contrib import admin
from .models import Assignment


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'subject',
        'created_by',
        'due_date',
        'is_published',
    )

    list_filter = (
        'is_published',
        'subject',
        'created_by',
    )

    search_fields = (
        'title',
        'description',
        'subject__name',
        'created_by__username',
    )

    ordering = ('due_date',)
