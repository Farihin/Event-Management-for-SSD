from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admins manage the application `role` here (the only place it can change)."""

    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Application role & profile", {"fields": ("role", "avatar")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Application role", {"fields": ("role",)}),
    )
