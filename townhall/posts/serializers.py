from rest_framework import serializers
from users.serializers import UserMiniSerializer
from .models import ReportedPost, User, Post, Comment


class CreateCommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ["id", "post", "content", "created_at"]


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

    image = serializers.ImageField(required=False, allow_null=True)

    comments = CommentSerializer(many=True, read_only=True, source="comment_set")

    liked_by = UserMiniSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "content",
            "created_at",
            "image",
            "likes",
            "liked_by",
            "comments",
        ]
        read_only_fields = ["id", "created_at", "likes", "liked_by", "comments", "user"]


class ReportedPostSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    post = PostSerializer(read_only=True)

    post_id = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(), write_only=True, source="post"
    )

    class Meta:
        model = ReportedPost
        fields = ["id", "user", "post", "post_id", "created_at"]
        read_only_fields = ["id", "created_at", "user", "post"]
