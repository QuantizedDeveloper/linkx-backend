from django.urls import path
from .views import (
    # Auth
    login_view,
    me_view,

    # Signup OTP flow
    send_signup_otp,
    verify_signup_otp,
    complete_signup,

    # Password reset
    forgot_password,
    verify_otp,
    reset_password,

    # App
    home_view,
)

urlpatterns = [
    # ---------- AUTH ----------
    path("login/", login_view),
    path("me/", me_view),

    # ---------- SIGNUP ----------
    path("send-signup-otp/", send_signup_otp),
    path("verify-signup-otp/", verify_signup_otp),
    path("complete-signup/", complete_signup),

    # ---------- PASSWORD RESET ----------
    path("forgot-password/", forgot_password),
    path("verify-reset-otp/", verify_otp),
    path("reset-password/", reset_password),

    # ---------- HOME ----------
    path("home/", home_view),
]

