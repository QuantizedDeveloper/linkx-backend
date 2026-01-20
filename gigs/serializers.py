from rest_framework import serializers
from .models import Gig



class GigSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gig
        fields = [
            'id',
            'title',
            'description',
            'tags',
            'gig_type',
            'price',
            'status',
            'created_at',
        ]
        read_only_fields = ['id', 'status', 'created_at']




class PublicGigSerializer(serializers.ModelSerializer):
    freelancer_name = serializers.CharField(
        source="freelancer.display_name", read_only=True
    )

    class Meta:
        model = Gig
        fields = [
            "id",
            "title",
            "description",
            "price",
            "price_type",
            "tags",
            "freelancer_name",
            "created_at",
        ]
        