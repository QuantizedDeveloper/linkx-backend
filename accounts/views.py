#complete_signup
# accounts/views.py (TOP of file)
#from insightface.app import FaceAnalysis

#face_model = FaceAnalysis(name="buffalo_l")
#face_model.prepare(ctx_id=0, det_size=(640, 640))



#import cv2

from rest_framework.response import Response

from .models import FaceEmbedding, EmailOTP
from django.contrib.auth.models import User




import json
import base64
import io
#import numpy as np
from io import BytesIO
from PIL import Image

#import face_recognition

from django.http import JsonResponse
from django.core.mail import send_mail
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

from .models import (
    User,
    EmailOTP,
    #UserFace,
    FaceEmbedding,
    PasswordResetOTP,
    PasswordResetToken,
)

#from .utils import (
    
#)


from django.db import transaction
from django.utils import timezone



from .models import User, EmailOTP, FaceEmbedding

from .utils import (
    validate_embedding,
    cosine_distance,
    check_same_person,
    canonical_embedding,
    generate_otp,
    otp_expiry,
    #otp_expiry_time,
    reset_token_expiry,
    #send_otp_via_brevo,
    send_otp_email
)




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

        # 🔥 Send OTP using Brevo
        send_otp_email(email, otp)

        return Response({"message": "OTP sent"})

    except Exception as e:
        print("🔥 SEND SIGNUP OTP ERROR:", e)
        return Response({"error": "Internal server error"}, status=500)


@api_view(["POST"])
def verify_signup_otp(request):
    email = request.data.get("email")
    otp = request.data.get("otp")

    if not email or not otp:
        return Response({"error": "Email and OTP required"}, status=400)

    # 🔒 Ensure same signup session
    #if request.session.get("email") != email:
       # return Response({"error": "Session mismatch"}, status=403)

    record = EmailOTP.objects.filter(
        email=email,
        otp=otp,
        purpose="signup",
        is_verified=False
    ).last()

    if not record:
        return Response({"error": "Invalid OTP"}, status=400)

    if record.is_expired():
        record.delete()
        return Response({"error": "OTP expired"}, status=400)

    record.is_verified = True
    record.save()

    # ✅ Mark email verified IN SESSION
    request.session["otp_verified"] = True

    return Response({"message": "OTP verified"})





@csrf_exempt
@api_view(["POST"])
def complete_signup(request):
    # 0️⃣ Get data from session
    email = request.session.get("email")
    username = request.session.get("username")
    password = request.session.get("password")

    embeddings_data = request.data.get("embeddings")

    if not all([email, username, password, embeddings_data]):
        return Response({"error": "Signup session expired"}, status=400)

    if not isinstance(embeddings_data, list) or len(embeddings_data) < MIN_FRAMES:
        return Response({"error": "Minimum 4 face captures required"}, status=400)

    # 1️⃣ OTP verification
    otp_record = EmailOTP.objects.filter(
        email=email, purpose="signup", is_verified=True
    ).last()
    if not otp_record:
        return Response({"error": "OTP not verified"}, status=400)

    # 2️⃣ Validate embeddings
    embeddings = []
    for idx, emb in enumerate(embeddings_data):
        if not validate_embedding(emb):
            return Response(
                {"error": f"Invalid embedding at index {idx}"},
                status=400
            )
        embeddings.append(np.array(emb, dtype=np.float32))

    # 3️⃣ Same-person consistency
    if not check_same_person(embeddings):
        return Response(
            {"error": "Face mismatch across captures"},
            status=400
        )

    # 4️⃣ Create canonical embedding
    canonical = canonical_embedding(embeddings)
    canonical /= np.linalg.norm(canonical)

    # 5️⃣ Duplicate detection
    for stored in FaceEmbedding.objects.only("embedding_vector"):
        stored_vec = np.array(stored.embedding_vector, dtype=np.float32)
        stored_vec /= np.linalg.norm(stored_vec)

        if cosine_distance(canonical, stored_vec) < DUPLICATE_THRESHOLD:
            return Response(
                {"error": "Face already registered"},
                status=409
            )

    # 6️⃣ Atomic user creation
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

    # 7️⃣ Auto-login
    refresh = RefreshToken.for_user(user)
    return Response({
        "access": str(refresh.access_token),
        "username": user.username
    })



@api_view(["POST"])
def login_view(request):
    email = request.data.get("email")
    password = request.data.get("password")

    try:
        user_obj = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"message": "Invalid credentials"}, status=401)

    user = authenticate(username=user_obj.username, password=password)

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


