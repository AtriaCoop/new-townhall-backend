from django.test import TestCase
from django.core.management import call_command

from posts.models import Comment

from posts.serializers import (
    CommentSerializer,
)


class TestCommentSerialization(TestCase):
    def setUp(self):
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/post_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/comment_fixture.json", verbosity=0)

    def test_comment_serializer_censors(self):
        comment = Comment(content="hell", anonymous=False, user=None)

        serializer = CommentSerializer(comment, context={"request": None})
        data = serializer.data

        self.assertEqual(data["content"], "****")
