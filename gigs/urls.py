from django.urls import path
from .views import upload_gig, list_gigs, search_gigs

urlpatterns = [
    path('upload/', upload_gig),
    path('', list_gigs),
    path('search/', search_gigs),
]
