from django.core.exceptions import ValidationError
from django.test import TestCase

from mentions.services import MentionServices
from mentions.types import CreateMentionData
from users.models import User


class TestMentionValidation(TestCase):
    def test_create_mentions_rejects_nonexistent_post(self):
        # Arrange
        mentioned_user = User.objects.create(email="mentioned@example.com")
        data = CreateMentionData(
            post_id=99999,
            mentioned_user_ids=[mentioned_user.id],
        )

        # Act and Assert
        with self.assertRaises(ValidationError):
            MentionServices.create_mentions(data)
