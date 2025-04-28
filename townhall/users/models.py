from django.db import models
from django.utils import timezone


class User(models.Model):
    username = models.CharField(max_length=127, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=127)
    full_name = models.CharField(max_length=127)
    pronouns = models.CharField(max_length=63, null=True, blank=True)
    title = models.CharField(max_length=63, null=True, blank=True)
    primary_organization = models.CharField(max_length=255, null=True, blank=True)
    other_organizations = models.TextField(null=True, blank=True)
    other_networks = models.TextField(null=True, blank=True)
    about_me = models.TextField(null=True, blank=True)
    skills_interests = models.TextField(null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_image", null=True, blank=True
    )
    profile_header = models.ImageField(
        upload_to="profile_header", null=True, blank=True
    )
    date_joined = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.username
