from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from .managers import UserManager
from django.utils import timezone
import uuid
from django.contrib.auth.models import User


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50)

    is_freelancer = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class EmailOTP(models.Model):
    PURPOSE_CHOICES = [
        ("signup", "Signup"),
        ("login", "Login"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    otp = models.CharField(max_length=4)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)

    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.email} - {self.otp}"


class FaceEmbedding(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    embedding_vector = models.JSONField()  # store 128-dim embedding
    is_blocked = models.BooleanField(default=False)
    blocked_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FaceEmbedding {self.user.email if self.user else 'Pending'}"



class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=4)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

class SignupSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField()
    username = models.CharField(max_length=50)
    password_hash = models.CharField(max_length=255)

    otp_verified = models.BooleanField(default=False)
    face_verified = models.BooleanField(default=False)

    face_embedding = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"SignupSession {self.email}"
        