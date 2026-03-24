"""Admin configuration for the users app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-date_creation"]
    list_display = ["email", "nom", "prenom", "role", "is_active", "is_staff", "date_creation"]
    list_filter = ["role", "is_active", "is_staff", "is_superuser"]
    search_fields = ["email", "nom", "prenom"]
    readonly_fields = ["id", "date_creation", "last_login"]

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Informations Personnelles", {"fields": ("nom", "prenom", "role", "equipe_id")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates Importantes", {"fields": ("last_login", "date_creation")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "nom", "prenom", "role", "is_active", "is_staff"),
            },
        ),
    )
