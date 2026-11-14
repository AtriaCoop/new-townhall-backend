from django.db import models
from django.utils import timezone
from posts.models import Post
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
    post = models.OneToOneField(
        Post, on_delete=models.SET_NULL, null=True, blank=True, related_name="event"
    )

    class Meta:
        ordering = ["date"]

    def delete(self, *args, **kwargs):
        if self.post:
            self.post.status = Post.Status.CANCELLED
            self.post.save(update_fields=["status"])

        return super().delete(*args, **kwargs)

    def __str__(self):
        return self.title
