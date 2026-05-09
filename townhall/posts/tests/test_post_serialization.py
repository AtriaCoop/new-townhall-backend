from django.test import TestCase
from django.core.management import call_command

from posts.serializers import (
    PostSerializer,
)

from posts.models import Post


class TestPostSerialization(TestCase):
    def setUp(self):
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/post_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/comment_fixture.json", verbosity=0)

    def test_post_serializer_censors_content(self):
        post = Post.objects.create(content="you BITCH!", anonymous=False, user=None)

        serializer = PostSerializer(post, context={"request": None})
        data = serializer.data

        self.assertEqual(
            data["content"],
            "you *****!",
        )

    def test_post_serializer_censors_list(self):
        posts = [
            Post.objects.create(content="shit happens", anonymous=False, user=None)
        ]

        serializer = PostSerializer(posts, many=True, context={"request": None})
        data = serializer.data

        self.assertEqual(data[0]["content"], "**** happens")
