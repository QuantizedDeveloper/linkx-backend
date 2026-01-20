from django.db.models import Q, Max

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from django.contrib.auth import get_user_model

from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from freelancers.models import FreelancerProfile
from django.contrib.auth import get_user_model

User = get_user_model()


class StartConversationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        freelancer_id = request.data.get('freelancer_id')

        freelancer = get_object_or_404(User, id=freelancer_id)

        # Ensure freelancer profile exists
        if not FreelancerProfile.objects.filter(user=freelancer).exists():
            return Response(
                {"error": "User is not a freelancer"},
                status=status.HTTP_400_BAD_REQUEST
            )

        conversation, created = Conversation.objects.get_or_create(
            client=request.user,
            freelancer=freelancer
        )

        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)

class SendMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)

        if request.user not in [conversation.client, conversation.freelancer]:
            return Response(
                {"error": "Not allowed"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                text=serializer.validated_data['text']
            )
            conversation.last_message_at = timezone.now()
            conversation.save()

            return Response({"success": True})

        return Response(serializer.errors, status=400)






class InboxView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        conversations = (
            Conversation.objects
            .filter(Q(client=user) | Q(freelancer=user))
            .annotate(last_message_time=Max('messages__created_at'))
            .order_by('-last_message_time')
        )

        data = []

        for convo in conversations:
            last_message = (
                convo.messages.order_by('-created_at').first()
            )

            other_user = (
                convo.freelancer if convo.client == user else convo.client
            )

            data.append({
                "conversation_id": convo.id,
                "other_user_id": other_user.id,
                "other_user_email": other_user.email,
                "last_message": last_message.text if last_message else "",
                "last_message_at": last_message.created_at if last_message else None,
            })

        return Response(data)
        