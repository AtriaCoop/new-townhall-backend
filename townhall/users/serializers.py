from rest_framework import serializers
import os

from .models import User


def validate_image_file(value):
    """Custom validator to ensure uploaded files are valid images"""
    if value:
        # Check file extension
        allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type not supported. Allowed types: "
                f"{', '.join(allowed_extensions)}"
            )

        # Check file size (max 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 5MB")


class UserSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()
    profile_header = serializers.SerializerMethodField()

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
            "profile_header",
            "date_joined",
        ]

    def get_profile_image(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None

    def get_profile_header(self, obj):
        if obj.profile_header:
            return obj.profile_header.url
        return None


class UserMiniSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "full_name", "primary_organization", "profile_image"]

    def get_profile_image(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None


class CreateUserSerializer(serializers.ModelSerializer):

    email = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "password"]


class UpdateUserSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False)
    pronouns = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    primary_organization = serializers.CharField(required=False, allow_blank=True)
    other_organizations = serializers.CharField(required=False, allow_blank=True)
    other_networks = serializers.CharField(required=False, allow_blank=True)
    about_me = serializers.CharField(required=False, allow_blank=True)
    skills_interests = serializers.CharField(required=False, allow_blank=True)
    profile_image = serializers.ImageField(
        required=False,
        allow_null=True,
        allow_empty_file=False,
        validators=[validate_image_file],
    )
    profile_header = serializers.ImageField(
        required=False,
        allow_null=True,
        allow_empty_file=False,
        validators=[validate_image_file],
    )

    def to_internal_value(self, data):
        """
        Convert string 'null' values to None and filter out empty strings
        """
        if hasattr(data, "_mutable"):
            data._mutable = True

        # Convert string 'null' values to None
        for field_name in [
            "full_name",
            "pronouns",
            "title",
            "primary_organization",
            "other_organizations",
            "other_networks",
            "about_me",
            "skills_interests",
        ]:
            if field_name in data and data[field_name] == "null":
                data[field_name] = None
            elif field_name in data and data[field_name] == "":
                data[field_name] = None

        return super().to_internal_value(data)

    # Make sure atleast 1 field has a Value
    def validate(self, data):
        if not data:
            raise serializers.ValidationError("At least 1 field must have a value")

        # Check if any field has a non-empty value (excluding None and empty strings)
        has_value = False
        for field, value in data.items():
            if value is not None and value != "" and value != "null":
                has_value = True
                break

        if not has_value:
            raise serializers.ValidationError(
                "At least 1 field must have a non-empty value"
            )

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)
    profile_header = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
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
            "profile_header",
        ]
