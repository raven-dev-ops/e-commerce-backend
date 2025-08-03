# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    # Add any custom fields you added to User in 'fieldsets' and 'add_fieldsets'
    fieldsets = DefaultUserAdmin.fieldsets + (
        ("Extra info", {"fields": ("phone_number",)}),
    )
    add_fieldsets = DefaultUserAdmin.add_fieldsets + (
        ("Extra info", {"fields": ("phone_number",)}),
    )
    list_display = (
        "username",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "phone_number",
    )
    search_fields = ("username", "email", "phone_number")
    list_filter = ("is_active", "is_staff", "is_superuser")
    ordering = ("username",)
