from rest_framework import serializers

from .models import User, Tag, Report


class UserSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()

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
            "date_joined",
            "receive_emails",
            "is_staff",
            "linkedin_url",
            "facebook_url",
            "x_url",
            "instagram_url",
        ]

    def get_profile_image(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


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


class OptionalURLField(serializers.URLField):
    def to_internal_value(self, data):
        if data == "":
            return None
        return super().to_internal_value(data)


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
    receive_emails = serializers.BooleanField(required=False)
    profile_image = serializers.ImageField(required=False, allow_null=True)
    tags = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
    linkedin_url = OptionalURLField(required=False, allow_blank=True, allow_null=True)
    facebook_url = OptionalURLField(required=False, allow_blank=True, allow_null=True)
    x_url = OptionalURLField(required=False, allow_blank=True, allow_null=True)
    instagram_url = OptionalURLField(required=False, allow_blank=True, allow_null=True)

    def validate_tags(self, value):
        """Custom validation for tags to ensure all items are strings"""
        # Check the raw input data before DRF processes it
        if "tags" in self.initial_data:
            raw_tags = self.initial_data["tags"]
            if isinstance(raw_tags, list):
                for tag in raw_tags:
                    if not isinstance(tag, str):
                        raise serializers.ValidationError("All tags must be strings")
        return value

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
            "linkedin_url",
            "facebook_url",
            "x_url",
            "instagram_url",
        ]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            "user_id",
            "content",
            "created_at",
        ]
