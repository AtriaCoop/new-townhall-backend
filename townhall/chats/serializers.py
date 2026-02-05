from rest_framework import serializers
from chats.models import Chat, Message, GroupMessage
from users.models import User
from users.serializers import UserMiniSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "profile_image", "title"]


class CreateChatSerializer(serializers.Serializer):
    name = serializers.CharField()
    participants = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )


class ChatSerializer(serializers.ModelSerializer):

    participants = UserProfileSerializer(many=True, read_only=True)

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

    chat = ChatMiniSerializer(read_only=True)
    chat_id = serializers.PrimaryKeyRelatedField(
        many=False, queryset=Chat.objects.all(), source="chat"
    )

    content = serializers.CharField(required=True, allow_blank=False)
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


class OptionalMessageSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(required=False)
    chat = ChatMiniSerializer(required=False)
    content = serializers.CharField(required=False)
    image_content = serializers.ImageField(required=False, allow_null=True)
    sent_at = serializers.DateTimeField(required=False)

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


class GroupMessageSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = GroupMessage
        fields = ["id", "user", "group_name", "content", "image", "sent_at"]
