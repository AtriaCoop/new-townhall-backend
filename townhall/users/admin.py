from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Tag


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "email",
        "full_name",
        "primary_organization",
        "is_staff",
        "is_active",
        "date_joined",
    ]
    list_filter = ["is_staff", "is_active", "date_joined"]
    search_fields = ["email", "full_name", "primary_organization"]
    ordering = ["-date_joined"]
    list_editable = ["is_staff"]

    # Override fieldsets since we use email, not username
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal Info",
            {
                "fields": (
                    "full_name",
                    "pronouns",
                    "title",
                    "primary_organization",
                    "other_organizations",
                    "about_me",
                    "skills_interests",
                )
            },
        ),
        (
            "Profile Media",
            {
                "fields": ("profile_image", "profile_header"),
            },
        ),
        (
            "Social Links",
            {
                "fields": (
                    "linkedin_url",
                    "facebook_url",
                    "x_url",
                    "instagram_url",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Security",
            {
                "fields": ("failed_login_attempts", "locked_until"),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "full_name", "is_staff"),
            },
        ),
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
