from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class Subscription(models.Model):
    PLAN_CHOICES = [
        ("free", "Free"),
        ("pro", "Pro"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # ✅ use settings.AUTH_USER_MODEL directly
        on_delete=models.CASCADE
    )
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    active = models.BooleanField(default=False)

    started_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # payment meta (important later)
    payment_provider = models.CharField(max_length=50, blank=True, null=True)
    payment_ref = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan}"
