from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display=('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter=('role', 'is_staff', 'is_active')
    fieldsets=UserAdmin.fieldsets+(('EduTrack Information', {'fields' : ('role',)}),)
    add_fieldsets=UserAdmin.add_fieldsets+(('EduTrack Information', {'fields' : ('role',)}),)
