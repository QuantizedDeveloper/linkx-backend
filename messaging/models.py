from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Conversation(models.Model):
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='client_conversations'
    )
    freelancer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='freelancer_conversations'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('client', 'freelancer')

    def __str__(self):
        return f"{self.client} ↔ {self.freelancer}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    text = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender}"
        