from rest_framework import serializers


class ActivitySerializer(serializers.Serializer):
    description = serializers.CharField(read_only=True)
    model = serializers.CharField(read_only=True)
    activity = serializers.DictField(read_only=True)
