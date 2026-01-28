from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model  # ✅ use this

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from freelancers.models import FreelancerProfile
from subscriptions.utils import freelancer_has_access
from .models import Gig
from .serializers import GigSerializer

User = get_user_model()  # ✅ ensures custom user is used

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_gig(request):
    user = request.user  # ✅ custom user

    # 1️⃣ Must be freelancer
    try:
        profile = FreelancerProfile.objects.get(user=user)
    except FreelancerProfile.DoesNotExist:
        return Response({"error": "Only freelancers can upload gigs"}, status=403)

    # 2️⃣ Subscription / trial access
    if not freelancer_has_access(profile):
        return Response({"error": "Subscription or active trial required"}, status=402)

    now = timezone.now()

    # 3️⃣ Rate limiting
    if Gig.objects.filter(freelancer=profile, created_at__gte=now - timedelta(hours=1)).count() >= 2:
        return Response({"error": "Gig upload limit: 2 per hour"}, status=429)

    if Gig.objects.filter(freelancer=profile, created_at__date=now.date()).count() >= 5:
        return Response({"error": "Gig upload limit: 5 per day"}, status=429)

    # 4️⃣ Validate input
    serializer = GigSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    # 5️⃣ Create gig
    gig = serializer.save(freelancer=profile, status="pending")

    return Response({"message": "Gig submitted for approval", "gig_id": gig.id}, status=201)


@api_view(["GET"])
def list_gigs(request):
    gigs = Gig.objects.filter(status="approved").order_by("-created_at")[:20]

    return Response([
        {
            "id": g.id,
            "title": g.title,
            "description": g.description,
            "price": g.price,
            "gig_type": g.gig_type,
            "tags": g.tags,
            "freelancer_name": g.freelancer.display_name,
        }
        for g in gigs
    ])


@api_view(["GET"])
def search_gigs(request):
    qs = Gig.objects.filter(status="approved")
    q = request.GET.get("q")
    tag = request.GET.get("tag")
    gig_type = request.GET.get("gig_type")

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if tag:
        qs = qs.filter(tags__contains=[tag])
    if gig_type:
        qs = qs.filter(gig_type=gig_type)

    qs = qs.order_by("-created_at")[:20]

    return Response([
        {
            "id": g.id,
            "title": g.title,
            "price": g.price,
            "gig_type": g.gig_type,
            "tags": g.tags,
            "freelancer": g.freelancer.display_name,
        }
        for g in qs
    ])
    
    



    