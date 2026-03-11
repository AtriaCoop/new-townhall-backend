from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "recipient",
        "notification_type",
        "actor",
        "target_id",
        "is_read",
        "created_at",
    ]
    list_filter = ["notification_type", "is_read"]
    search_fields = ["recipient__email", "actor__email"]
    ordering = ["-created_at"]
