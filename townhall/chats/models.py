from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords
from users.models import User
from cloudinary.models import CloudinaryField


class Chat(models.Model):
    participants = models.ManyToManyField(User, related_name="chats")
    hidden_by = models.ManyToManyField(User, related_name="hidden_chats", blank=True)
    name = models.CharField(max_length=127)
    created_at = models.DateTimeField(default=timezone.now)
    history = HistoricalRecords()

    def __str__(self):
        return str(self.id)


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    content = models.TextField()
    image_content = CloudinaryField("image", null=True, blank=True)
    sent_at = models.DateTimeField(default=timezone.now)
    history = HistoricalRecords()

    def __str__(self):
        return str(self.id)


class ChatReadStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    last_read_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "chat")

    def __str__(self):
        return f"User {self.user_id} - Chat {self.chat_id}"


class GroupMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group_name = models.CharField(max_length=100)
    content = models.TextField()
    image = CloudinaryField("image", blank=True, null=True)
    sent_at = models.DateTimeField(default=timezone.now)
    history = HistoricalRecords()

    def __str__(self):
        return str(self.id)
