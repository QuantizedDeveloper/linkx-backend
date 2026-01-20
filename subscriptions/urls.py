from django.urls import path
from .views import ActivateSubscriptionView

urlpatterns = [
    path('activate-test/', ActivateSubscriptionView.as_view()),
]
