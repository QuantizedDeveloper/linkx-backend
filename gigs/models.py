from django.db import models
from freelancers.models import FreelancerProfile


class Gig(models.Model):
    GIG_TYPE_CHOICES = [
        ('fixed', 'Fixed Price'),
        ('hourly', 'Hourly'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    freelancer = models.ForeignKey(
        FreelancerProfile,
        on_delete=models.CASCADE,
        related_name='gigs'
    )

    title = models.CharField(max_length=120)
    description = models.TextField()

    tags = models.JSONField(default=list, blank=True)

    gig_type = models.CharField(
        max_length=10,
        choices=GIG_TYPE_CHOICES,
        default='fixed'   # ✅ fixes migration issue
    )

    price = models.PositiveIntegerField()
    delivery_days = models.PositiveIntegerField(default=1)

    image1 = models.ImageField(
        upload_to='gigs/',
        null=True,
        blank=True
    )
    image2 = models.ImageField(
        upload_to='gigs/',
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
        

        
