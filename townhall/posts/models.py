from django.db import models
from django.utils import timezone
from users.models import User
from cloudinary.models import CloudinaryField
from simple_history.models import HistoricalRecords


class Post(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    image = CloudinaryField("image", blank=True, null=True)
    likes = models.IntegerField(default=0)
    liked_by = models.ManyToManyField(User, blank=True, related_name="liked_posts")
    history = HistoricalRecords()
    pinned = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    history = HistoricalRecords()

    def __str__(self):
        return str(self.id)


class ReportedPost(models.Model):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    history = HistoricalRecords()

    def __str__(self):
        return str(self.id)


class Reaction(models.Model):
    Reaction_Choices = [
        ("love", "Love"),
        ("appreciate", "Appreciate"),
        ("respect", "Respect"),
        ("support", "Support"),
        ("inspired", "Inspired"),
        ("helpful", "Helpful"),
    ]

    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=20, choices=Reaction_Choices)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ["post", "user", "reaction_type"]

    def __str__(self):
        return f"{self.user.full_name} - {self.reaction_type} on Post {self.post.id}"
