from django.urls import path
from .views import (
    start_freelancing,
    get_profile,
    update_profile,
    freelancer_profile,
    freelancer_gigs,
    freelancer_payment_info
)




urlpatterns = [
    # private
    path("start/", start_freelancing),
    path("me/", get_profile),
    path("me/update/", update_profile),
    path("payment-info/<int:freelancer_id>/", freelancer_payment_info),

    # public
    path("<int:freelancer_id>/", freelancer_profile),
    path("<int:freelancer_id>/gigs/", freelancer_gigs),
]



