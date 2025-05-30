from rest_framework import serializers
from chats.models import Chat, Message
from users.models import User
from users.serializers import UserMiniSerializer


class ChatSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all()
    )

    class Meta:
        model = Chat
        fields = ["id", "name", "participants", "created_at"]
        read_only_fields = ["id", "created_at"]


class ChatMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ["id", "name"]


class MessageSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        many=False, queryset=User.objects.all(), source="user"
    )

    chat = ChatMiniSerializer(read_only=True)
    chat_id = serializers.PrimaryKeyRelatedField(
        many=False, queryset=Chat.objects.all(), source="chat"
    )

    content = serializers.CharField(required=True, allow_blank=False)
    image_content = serializers.ImageField(required=False, allow_null=True)
    image_content = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "user",
            "user_id",
            "chat",
            "chat_id",
            "content",
            "image_content",
            "sent_at",
        ]
        read_only_fields = ["id"]
