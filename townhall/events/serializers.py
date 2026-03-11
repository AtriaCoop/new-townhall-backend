from rest_framework import serializers
from users.serializers import UserMiniSerializer
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    admin = UserMiniSerializer(read_only=True)
    participants = UserMiniSerializer(many=True, read_only=True)
    isEnrolled = serializers.SerializerMethodField()

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
        ]
        read_only_fields = ["id", "admin", "participants", "created_at"]

    def get_isEnrolled(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return any(p.id == request.user.id for p in obj.participants.all())
        return False


class CreateEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["title", "description", "date", "time", "location"]
