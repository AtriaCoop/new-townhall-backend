from django.db import models
from django.utils import timezone
from users.models import User


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("reaction", "Reaction on post"),
        ("comment", "Comment on post"),
        ("like", "Like on post"),
        ("new_event", "New event created"),
        ("event_update", "Event updated"),
        ("event_cancel", "Event canceled"),
        ("event_reminder", "Event reminder"),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="caused_notifications",
        null=True,
        blank=True,
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    target_id = models.IntegerField(null=True, blank=True)
    detail = models.CharField(max_length=255, blank=True, default="")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "-created_at"]),
            models.Index(fields=["recipient", "is_read"]),
        ]

    def __str__(self):
        return f"{self.notification_type} for user {self.recipient_id}"
