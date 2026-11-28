from django.test import TestCase
from django.utils import timezone

from mentions.models import Mention
from posts.services import PostServices
from posts.types import CreatePostData
from users.models import User


class TestPostMentions(TestCase):
    def test_create_post_saves_mentions(self):
        author = User.objects.create(email="author@example.com")
        mentioned_user = User.objects.create(email="mentioned@example.com")
        post_data = CreatePostData(
            user_id=author.id,
            content="Hello @mentioned",
            created_at=timezone.now(),
            mentioned_user_ids=[mentioned_user],
        )

        post = PostServices.create_post(post_data)

        self.assertTrue(
            Mention.objects.filter(
                post=post,
                mentioned_user=mentioned_user,
            ).exists()
        )
