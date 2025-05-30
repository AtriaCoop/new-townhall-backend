from rest_framework import serializers
from chats.models import Chat
from users.models import User
from chats.models import Message


class MessageSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Message
        fields = ["id", "user", "chat", "content", "image_content", "sent_at"]
        

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "profile_image", "title"] 


class ChatSerializer(serializers.ModelSerializer):
    
    participants = UserProfileSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ["id", "name", "participants", "created_at"]
        read_only_fields = ["id", "created_at"]
