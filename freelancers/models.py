from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta

class FreelancerProfile(models.Model):
    STATUS_CHOICES = [
        ('incomplete', 'Incomplete'),
        ('trial_active', 'Trial Active'),
        ('trial_expired', 'Trial Expired'),
        ('approved', 'Approved'),
        ('suspended', 'Suspended'),
        ('banned', 'Banned'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # ✅ correct usage
        on_delete=models.CASCADE
    )
    display_name = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='incomplete'
    )

    trial_started_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
   
    # Payment fields
    upi_id = models.CharField(max_length=100, blank=True)
    razorpay_link = models.URLField(blank=True)
    instamojo_link = models.URLField(blank=True)
    payment_note = models.CharField(
        max_length=200,
        blank=True,
        help_text="Shown to client before payment"
    )

    upi_qr = models.ImageField(
        upload_to="payments/qr/",
        null=True,
        blank=True
    )
    custom_payment_label = models.CharField(max_length=50, blank=True, null=True)
    custom_payment_details = models.TextField(blank=True, null=True)
    
    def start_trial(self):
        self.trial_started_at = timezone.now()
        self.trial_ends_at = timezone.now() + timedelta(days=28)
        self.status = 'trial_active'
        self.save()

    def __str__(self):
        return f"{self.user.email} freelancer"
