from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import FreelancerProfile
from .serializers import FreelancerPublicSerializer
from gigs.models import Gig
from gigs.serializers import PublicGigSerializer


# ============================
# PRIVATE (AUTH REQUIRED)
# ============================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_freelancing(request):
    user = request.user

    if user.is_freelancer:
        return Response(
            {"error": "User is already a freelancer"},
            status=400
        )

    profile = FreelancerProfile.objects.create(
        user=user,
        display_name=user.username,
        status="trial_active"
    )

    profile.start_trial()

    user.is_freelancer = True
    user.save()

    return Response({
        "message": "Freelancer trial started",
        "status": profile.status,
        "trial_ends_at": profile.trial_ends_at
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    user = request.user

    if not user.is_freelancer:
        return Response(
            {"error": "User is not a freelancer"},
            status=403
        )

    profile = get_object_or_404(FreelancerProfile, user=user)

    return Response({
    "display_name": profile.display_name,
    "description": profile.description,
    "tags": profile.tags,

    "payments": {
        "razorpay": profile.razorpay_link,
        "instamojo": profile.instamojo_link,
        "upi_id": profile.upi_id,
        "qr": request.build_absolute_uri(profile.payment_qr.url)
              if profile.payment_qr else None,
        "custom": {
            "label": profile.custom_payment_label,
            "details": profile.custom_payment_details
        } if profile.custom_payment_label else None
     }
   })



@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user

    if not user.is_freelancer:
        return Response(
            {"error": "User is not a freelancer"},
            status=403
        )

    profile = get_object_or_404(FreelancerProfile, user=user)

    profile.display_name = request.data.get(
        "display_name", profile.display_name
    )
    profile.description = request.data.get(
        "description", profile.description
    )
    profile.tags = request.data.get(
        "tags", profile.tags
    )
    profile.upi_id = request.data.get("upi_id", profile.upi_id)
    profile.razorpay_link = request.data.get("razorpay_link", profile.razorpay_link)
    profile.instamojo_link = request.data.get("instamojo_link", profile.instamojo_link)
    profile.payment_note = request.data.get("payment_note", profile.payment_note)
    if "upi_qr" in request.FILES:
      profile.upi_qr = request.FILES["upi_qr"]
    
    

    # Move incomplete → trial_active automatically
    if (
        profile.display_name
        and profile.description
        and profile.tags
        and profile.status == "incomplete"
    ):
        profile.status = "trial_active"

    profile.save()

    return Response({
        "message": "Profile updated successfully",
        "status": profile.status
    })


# ============================
# PUBLIC (NO AUTH)
# ============================

@api_view(['GET'])
def freelancer_profile(request, freelancer_id):
    """
    Public freelancer profile (like X profile page)
    """
    profile = get_object_or_404(
        FreelancerProfile,
        id=freelancer_id,
        status__in=["trial_active", "approved"]
    )

    serializer = FreelancerPublicSerializer(profile)
    return Response(serializer.data)


@api_view(['GET'])
def freelancer_gigs(request, freelancer_id):
    """
    Public list of all approved gigs by a freelancer
    (like tweets on profile)
    """
    gigs = Gig.objects.filter(
        freelancer_id=freelancer_id,
        status="approved"
    ).order_by("-created_at")

    serializer = PublicGigSerializer(gigs, many=True)
    return Response(serializer.data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def freelancer_payment_info(request, freelancer_id):
    profile = get_object_or_404(
        FreelancerProfile,
        id=freelancer_id,
        status__in=["trial_active", "approved"]
    )

    return Response({
        "upi_id": profile.upi_id,
        "razorpay_link": profile.razorpay_link,
        "instamojo_link": profile.instamojo_link,
        "payment_note": profile.payment_note,
        "upi_qr": profile.upi_qr.url if profile.upi_qr else None,
    })
    