from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from .models import Subscription
from freelancers.models import FreelancerProfile


class ActivateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not FreelancerProfile.objects.filter(user=user).exists():
            return Response({"error": "Not a freelancer"}, status=403)

        sub, created = Subscription.objects.get_or_create(
            user=user,
            defaults={
                'plan': 'freelancer_basic',
                'ends_at': timezone.now() + timedelta(days=30),
            }
        )

        if not created:
            sub.ends_at = timezone.now() + timedelta(days=30)
            sub.status = 'active'
            sub.save()

        return Response({"message": "Subscription activated (TEST MODE)"})
        