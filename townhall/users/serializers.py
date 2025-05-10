from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "pronouns",
            "title",
            "primary_organization",
            "other_organizations",
            "other_networks",
            "about_me",
            "skills_interests",
            "profile_image",
        ]


class CreateUserSerializer(serializers.ModelSerializer):

    email = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "email",
            "password"
        ]


class UpdateUserSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    pronouns = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    primary_organization = serializers.CharField(required=False, allow_blank=True)
    other_organizations = serializers.CharField(required=False, allow_blank=True)
    other_networks = serializers.CharField(required=False, allow_blank=True)
    about_me = serializers.CharField(required=False, allow_blank=True)
    skills_interests = serializers.CharField(required=False, allow_blank=True)
    profile_image = serializers.ImageField(required=False, allow_null=True)

    # Make sure atleast 1 field has a Value
    def validate(self, data):
        if all(data.get(field) is None for field in data):
            raise serializers.ValidationError("Atleast 1 field must have a Value")
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            "full_name", "email", "pronouns", "title",
            "primary_organization", "other_organizations", "other_networks",
            "about_me", "skills_interests", "profile_image"
        ]
