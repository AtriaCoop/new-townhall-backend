from django.db import models
from django.utils import timezone
from users.models import User


class Post(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    content = models.TextField()
    image_content = models.ImageField(upload_to="post_images", null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.id)


class Comment(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    post_id = models.ForeignKey(Post, on_delete=models.DO_NOTHING)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.id)
