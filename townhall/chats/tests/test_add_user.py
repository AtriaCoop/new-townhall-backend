from django.test import TestCase
from django.core.management import call_command
from django.core.exceptions import ValidationError
from unittest.mock import patch

from chats.models import Chat
from chats.daos import ChatDao
from chats.services import ChatServices
from users.models import User


class TestAddUser(TestCase):
    def setUp(self):
        call_command("loaddata", "fixtures/chat_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)

        chat = Chat.objects.get(pk=3)
        bob = User.objects.get(pk=1)
        jerome = User.objects.get(pk=2)
        chat.participants.add(bob, jerome)

    def test_add_user_success(self):
        chat_id = 3
        user_to_add = User.objects.create(
            id=999, email="alice@example.com", full_name="alice"
        )

        chat = Chat.objects.get(id=chat_id)
        self.assertFalse(
            chat.participants.filter(id=user_to_add.id).exists(),
            "user should not be in chat before being added",
        )

        ChatDao.add_user(chat_id=chat_id, user_id=user_to_add.id)

        chat.refresh_from_db()
        self.assertTrue(
            chat.participants.filter(id=user_to_add.id).exists(),
            "User should be in chat participants after being added",
        )

    @patch("chats.daos.ChatDao.add_user")
    def test_add_user_chat_not_found(self, mock_add_user):
        mock_add_user.side_effect = ValidationError("Chat id 9999 does not exist")
        chat_id = 9999
        user_id = 1
        with self.assertRaises(ValidationError) as context:
            ChatServices.add_user(chat_id=chat_id, user_id=user_id)

        self.assertIn("does not exist", str(context.exception))

    def test_add_user_already_participant(self):
        chat_id = 3
        with self.assertRaises(ValidationError) as context:
            ChatDao.add_user(chat_id=chat_id, user_id=1)

        self.assertIn("is already a participant", str(context.exception))
