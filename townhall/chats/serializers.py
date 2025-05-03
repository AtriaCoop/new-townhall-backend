from rest_framework import serializers
from .models import Chat
from ..users.models import User


class ChatSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all()
    )

    class Meta:
        model = Chat
        fields = ["id", "name", "participants", "created_at"]
        read_only_fields = ["id", "created_at"]
