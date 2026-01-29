import json
from PIL import Image
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

import numpy as np  # ✅ REQUIRED (you use np later)

from .models import (
    User,
    EmailOTP,
    FaceEmbedding,
    PasswordResetOTP,
    PasswordResetToken,
)

from .utils import (
    validate_embedding,
    cosine_distance,
    check_same_person,
    canonical_embedding,
    generate_otp,
    otp_expiry,
    reset_token_expiry,
    send_otp_email,
)

# ✅ If these are not defined elsewhere, define them here (minimum safe defaults)
MIN_FRAMES = 4
DUPLICATE_THRESHOLD = 0.35


@csrf_exempt
@api_view(["POST"])
def send_signup_otp(request):
    try:
        email = request.data.get("email")
        username = request.data.get("username")
        password = request.data.get("password")

        if not all([email, username, password]):
            return Response({"error": "Missing fields"}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already registered"}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already taken"}, status=400)

        # Store signup data in session
        request.session["email"] = email
        request.session["username"] = username
        request.session["password"] = password
        request.session["otp_verified"] = False
        request.session.set_expiry(600)

        # Remove old OTPs
        EmailOTP.objects.filter(email=email, purpose="signup").delete()

        otp = generate_otp()

        EmailOTP.objects.create(
            email=email,
            otp=otp,
            purpose="signup",
            expires_at=otp_expiry(),
        )

        # Send OTP
        send_otp_email(email, otp)

        return Response({"message": "OTP sent"})

    except Exception as e:
        print("🔥 SEND SIGNUP OTP ERROR:", e)
        return Response({"error": "Internal server error"}, status=500)
        
        




@api_view(["POST"])
def verify_signup_otp(request):
    email = str(request.data.get("email", "")).strip().lower()
    otp = str(request.data.get("otp", "")).strip()

    if not email or not otp:
        return Response({"error": "Email and OTP required"}, status=400)

    # DEBUG: show last OTPs for that email
    last_records = list(
        EmailOTP.objects.filter(email=email)
        .order_by("-id")
        .values("id", "email", "otp", "purpose", "is_verified", "created_at")[:5]
    )

    print("INPUT EMAIL:", email)
    print("INPUT OTP:", otp)
    print("LAST RECORDS:", last_records)

    # Now try to match normally
    record = EmailOTP.objects.filter(
        email=email,
        otp=otp,
        purpose="signup",
        is_verified=False
    ).order_by("-id").first()

    if not record:
        return Response({
            "error": "Invalid OTP",
            "debug": {
                "email": email,
                "otp": otp,
                "last_records": last_records
            }
        }, status=400)

    if record.is_expired():
        record.delete()
        return Response({"error": "OTP expired"}, status=400)

    record.is_verified = True
    record.save()

    request.session["otp_verified"] = True
    request.session["otp_verified_email"] = email

    return Response({"message": "OTP verified"}, status=200)





@csrf_exempt
@api_view(["POST"])
def complete_signup(request):
    # Get data from session
    email = request.session.get("email")
    username = request.session.get("username")
    password = request.session.get("password")

    embeddings_data = request.data.get("embeddings")

    if not all([email, username, password, embeddings_data]):
        return Response({"error": "Signup session expired"}, status=400)

    if not isinstance(embeddings_data, list) or len(embeddings_data) < MIN_FRAMES:
        return Response({"error": "Minimum 4 face captures required"}, status=400)

    # OTP verification
    otp_record = EmailOTP.objects.filter(
        email=email, purpose="signup", is_verified=True
    ).last()
    if not otp_record:
        return Response({"error": "OTP not verified"}, status=400)

    # Validate embeddings
    embeddings = []
    for idx, emb in enumerate(embeddings_data):
        if not validate_embedding(emb):
            return Response(
                {"error": f"Invalid embedding at index {idx}"},
                status=400
            )
        embeddings.append(np.array(emb, dtype=np.float32))

    # Same-person consistency
    if not check_same_person(embeddings):
        return Response(
            {"error": "Face mismatch across captures"},
            status=400
        )

    # Create canonical embedding
    canonical = canonical_embedding(embeddings)
    canonical /= np.linalg.norm(canonical)

    # Duplicate detection
    for stored in FaceEmbedding.objects.only("embedding_vector"):
        stored_vec = np.array(stored.embedding_vector, dtype=np.float32)
        stored_vec /= np.linalg.norm(stored_vec)

        if cosine_distance(canonical, stored_vec) < DUPLICATE_THRESHOLD:
            return Response(
                {"error": "Face already registered"},
                status=409
            )

    # Atomic user creation
    with transaction.atomic():
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password
        )
        FaceEmbedding.objects.create(
            user=user,
            embedding_vector=canonical.tolist()
        )
        otp_record.delete()

        # clear session
        for k in ("email", "username", "password"):
            request.session.pop(k, None)

    # Auto-login
    refresh = RefreshToken.for_user(user)
    return Response({
        "access": str(refresh.access_token),
        "username": user.username
    })


@api_view(["POST"])
def login_view(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response({"message": "Invalid credentials"}, status=401)

    # ✅ Correct authentication for custom user where USERNAME_FIELD='email'
    user = authenticate(request, email=email, password=password)

    if not user:
        return Response({"message": "Invalid credentials"}, status=401)

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "username": user.username
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user
    return Response({
        "email": user.email,
        "username": user.username,
        "is_freelancer": user.is_freelancer,
        "is_staff": user.is_staff
    })


@csrf_exempt
def forgot_password(request):
    data = json.loads(request.body)
    email = data.get("email")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({"message": "User does not exist"}, status=404)

    # delete old OTPs
    PasswordResetOTP.objects.filter(user=user).delete()

    otp = generate_otp()

    PasswordResetOTP.objects.create(
        user=user,
        otp=otp,
        expires_at=otp_expiry()
    )

    # send email here
    print("OTP:", otp)

    return JsonResponse({"message": "OTP sent"})


@csrf_exempt
def verify_otp(request):
    data = json.loads(request.body)
    email = data.get("email")
    otp_input = data.get("otp")

    try:
        user = User.objects.get(email=email)
        otp_obj = PasswordResetOTP.objects.get(user=user)
    except:
        return JsonResponse({"message": "Invalid or expired OTP"}, status=400)

    if otp_obj.is_expired():
        otp_obj.delete()
        return JsonResponse({"message": "OTP expired"}, status=400)

    if otp_obj.otp != otp_input:
        otp_obj.attempts += 1
        otp_obj.save()

        if otp_obj.attempts >= 3:
            otp_obj.delete()
            return JsonResponse({"message": "OTP expired. New OTP required"}, status=400)

        return JsonResponse({"message": "Incorrect OTP"}, status=400)

    # OTP valid
    otp_obj.delete()

    reset_token = PasswordResetToken.objects.create(
        user=user,
        expires_at=reset_token_expiry()
    )

    return JsonResponse({
        "reset_token": str(reset_token.token),
        "username": user.username
    })


@csrf_exempt
def reset_password(request):
    data = json.loads(request.body)
    token = data.get("reset_token")
    new_password = data.get("new_password")

    try:
        reset = PasswordResetToken.objects.get(token=token)
    except PasswordResetToken.DoesNotExist:
        return JsonResponse({"message": "Invalid token"}, status=400)

    if reset.expires_at < timezone.now():
        reset.delete()
        return JsonResponse({"message": "Token expired"}, status=400)

    user = reset.user
    user.password = make_password(new_password)
    user.save()

    reset.delete()

    return JsonResponse({"message": "Password reset successful"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def home_view(request):
    return Response({
        "message": "Welcome",
        "username": request.user.username
    })
    