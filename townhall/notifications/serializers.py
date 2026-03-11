from rest_framework import serializers
from users.serializers import UserMiniSerializer
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor = UserMiniSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "actor",
            "notification_type",
            "target_id",
            "detail",
            "is_read",
            "created_at",
        ]
        read_only_fields = fields
