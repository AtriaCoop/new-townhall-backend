from django.test import TestCase

from mentions.models import Mention
from mentions.services import MentionServices
from mentions.types import CreateMentionData
from posts.models import Post
from users.models import User


class TestMentionService(TestCase):
    def test_create_mentions_success(self):
        # Arrange
        author = User.objects.create(email="author@example.com")
        mentioned_user = User.objects.create(email="mentioned@example.com")
        post = Post.objects.create(content="Hello @mentioned", user=author)
        data = CreateMentionData(
            post_id=post.id,
            mentioned_user_ids=[mentioned_user.id],
        )

        # Act
        MentionServices.create_mentions(data)

        # Assert
        mention = Mention.objects.get(post=post)
        self.assertEqual(mention.mentioned_user_id, mentioned_user.id)

    def test_create_mentions_ignores_duplicate_mentions(self):
        # Arrange
        author = User.objects.create(email="author@example.com")
        mentioned_user = User.objects.create(email="mentioned@example.com")
        post = Post.objects.create(content="Hello @mentioned", user=author)
        data = CreateMentionData(
            post_id=post.id,
            mentioned_user_ids=[mentioned_user.id, mentioned_user.id],
        )

        # Act
        MentionServices.create_mentions(data)

        # Assert
        self.assertEqual(
            Mention.objects.filter(
                post=post,
                mentioned_user=mentioned_user,
            ).count(),
            1,
        )
