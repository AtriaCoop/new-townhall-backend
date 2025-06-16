from rest_framework import serializers
from users.serializers import UserMiniSerializer
from .models import User, Post, Comment


class CreateCommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ["id", "user", "post", "content", "created_at"]


class CommentUserMiniSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "full_name", "profile_image"]

    def get_profile_image(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None


class CommentSerializer(serializers.ModelSerializer):
    user = CommentUserMiniSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "user", "post", "content", "created_at"]


class PostSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source="user"
    )

    image = serializers.ImageField(required=False, allow_null=True)

    comments = CommentSerializer(many=True, read_only=True, source="comment_set")

    liked_by = UserMiniSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ["id", "user", "user_id",
                  "content", "created_at", "image",
                  "likes", "liked_by", "comments"]
        read_only_fields = ["id", "created_at", "likes", "liked_by", "comments"]
