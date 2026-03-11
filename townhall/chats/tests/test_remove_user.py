from django.test import TestCase
from django.core.management import call_command
from django.core.exceptions import ValidationError
from unittest.mock import patch

from chats.models import Chat
from chats.daos import ChatDao
from chats.services import ChatServices
from users.models import User


class TestRemoveUser(TestCase):
    def setUp(self):
        call_command("loaddata", "fixtures/chat_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)

        chat = Chat.objects.get(pk=3)
        bob = User.objects.get(pk=1)
        jerome = User.objects.get(pk=2)
        chat.participants.add(bob, jerome)

    def test_remove_user_success(self):
        """Test successful removal of a user from a chat."""
        chat_id = 3
        user_to_remove_id = 1

        chat = Chat.objects.get(id=chat_id)
        self.assertTrue(
            chat.participants.filter(id=user_to_remove_id).exists(),
            "User should be in chat before removal.",
        )

        ChatDao.remove_user(chat_id=chat_id, user_id=user_to_remove_id)

        chat.refresh_from_db()
        self.assertFalse(
            chat.participants.filter(id=user_to_remove_id).exists(),
            "User should be removed from chat participants.",
        )

    @patch("chats.daos.ChatDao.remove_user")
    def test_remove_user_chat_not_found(self, mock_remove_user):
        # Test removal fails when chat doesn't exist.

        mock_remove_user.side_effect = ValidationError(
            "Chat with id 9999 does not exist."
        )
        chat_id = 9999
        user_id = 1

        with self.assertRaises(ValidationError) as context:
            ChatServices.remove_user(chat_id=chat_id, user_id=user_id)

        self.assertIn("does not exist", str(context.exception))

    def test_remove_user_not_participant(self):
        # Test removal fails when user is not a participant.

        chat_id = 3
        non_participant_user = User.objects.create(
            id=999, email="notinchat@example.com", full_name="Not In Chat"
        )

        with self.assertRaises(ValidationError) as context:
            ChatDao.remove_user(chat_id=chat_id, user_id=non_participant_user.id)

        self.assertIn("not a participant", str(context.exception))
