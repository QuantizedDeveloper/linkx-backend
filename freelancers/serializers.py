from rest_framework import serializers
from .models import FreelancerProfile


class FreelancerPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = FreelancerProfile
        fields = [
            "id",
            "display_name",
            "description",
            "tags",
            "status",
            "created_at",
        ]
        