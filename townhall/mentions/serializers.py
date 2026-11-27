from rest_framework import serializers

from posts.models import Post
from users.models import User
from .models import Mention

from posts.serializers import PostSerializer
from users.serializers import UserMiniSerializer


class MentionSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    mentioned_user = UserMiniSerializer(read_only=True)

    post_id = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(), source="post", write_only=True
    )

    mentioned_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="mentioned_user", write_only=True
    )

    class Meta:
        model = Mention
        fields = [
            "id",
            "post",
            "mentioned_user",
            "post_id",
            "mentioned_user_id",
        ]
