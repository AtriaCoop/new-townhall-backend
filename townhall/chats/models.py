from django.db import models
from django.utils import timezone
from users.models import User


class Chat(models.Model):
    participants = models.ManyToManyField(User, related_name="chats")
    name = models.CharField(max_length=127)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.id)
    

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    chat = models.ForeignKey(Chat, on_delete=models.DO_NOTHING)
    content = models.TextField()
    image_content = models.ImageField(upload_to="post_images", null=True, blank=True)
    sent_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.id)