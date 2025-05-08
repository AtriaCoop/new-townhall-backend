from django.db import models
from django.utils import timezone
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Hash password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    full_name = models.CharField(max_length=127, null=True, blank=True)
    pronouns = models.CharField(max_length=63, null=True, blank=True)
    title = models.CharField(max_length=63, null=True, blank=True)
    primary_organization = models.CharField(max_length=255, null=True, blank=True)
    other_organizations = models.TextField(null=True, blank=True)
    other_networks = models.TextField(null=True, blank=True)
    about_me = models.TextField(null=True, blank=True)
    skills_interests = models.TextField(null=True, blank=True)
    profile_image = models.ImageField(
        upload_to="profile_image", null=True, blank=True
    )
    profile_header = models.ImageField(
        upload_to="profile_header", null=True, blank=True
    )
    date_joined = models.DateTimeField(default=timezone.now)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Required for admin panel access

    objects = UserManager()

    USERNAME_FIELD = 'email'  # for authentication
    REQUIRED_FIELDS = []      # email is required by default

    def __str__(self):
        return self.email
