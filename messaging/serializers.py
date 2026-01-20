from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.ReadOnlyField(source='sender.email')

    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_email', 'text', 'created_at']
        read_only_fields = ['id', 'created_at', 'sender']


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'client', 'freelancer', 'messages', 'created_at']
        read_only_fields = ['id', 'created_at']
        