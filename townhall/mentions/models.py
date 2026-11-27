from django.db import models

from posts.models import Post
from users.models import User


class Mention(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="mentions")
    mentioned_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="mentions_received"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "mentioned_user"],
                name="unique_post_mentioned_user",
            )
        ]

    def __str__(self):
        return f"Post ID: {self.post_id} | Mentioned User ID: {self.mentioned_user_id}"
