from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "identity_user"

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=100, blank=True)
    notification_email = models.EmailField(blank=True)  # can differ from login email
    phone = models.CharField(max_length=20, blank=True)
    timezone = models.CharField(max_length=50, default="America/Sao_Paulo")

    class Meta:
        db_table = "identity_user_profile"

    def __str__(self):
        return f"Profile({self.user.email})"
