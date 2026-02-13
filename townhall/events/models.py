from django.db import models
from django.utils import timezone
from users.models import User
from simple_history.models import HistoricalRecords


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    date = models.DateField()
    time = models.CharField(max_length=63)  # e.g. "9:00 AM - 12:00 PM"
    location = models.CharField(max_length=255)
    admin = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_events"
    )
    participants = models.ManyToManyField(
        User, blank=True, related_name="enrolled_events"
    )
    created_at = models.DateTimeField(default=timezone.now)
    history = HistoricalRecords()

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return self.title
