from rest_framework import serializers
from users.serializers import UserMiniSerializer
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    admin = UserMiniSerializer(read_only=True)
    participants = UserMiniSerializer(many=True, read_only=True)
    isEnrolled = serializers.SerializerMethodField()
    hasPost = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "date",
            "time",
            "location",
            "admin",
            "participants",
            "isEnrolled",
            "created_at",
            "hasPost",
        ]
        read_only_fields = ["id", "admin", "participants", "created_at"]

    def get_isEnrolled(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return any(p.id == request.user.id for p in obj.participants.all())
        return False

    def get_hasPost(self, obj):
        return obj.post is not None


class CreateEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["title", "description", "date", "time", "location"]


class ShareEventSearializer(serializers.Serializer):
    share_to_newsfeed = serializers.BooleanField()
