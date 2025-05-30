from django.test import TestCase
from django.core.management import call_command
from unittest.mock import patch
from django.core.exceptions import ValidationError
from chats.models import Chat, Message
from users.models import User
from chats.types import CreateMessageData
from chats.services import MessageServices
from django.utils import timezone
from datetime import datetime


class TestMessageService(TestCase):
    def setUp(self):
        call_command("loaddata", "fixtures/chat_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/message_fixture.json", verbosity=0)

        message = Message.objects.get(pk=3)
        chat = Chat.objects.get(pk=3)
        bob = User.objects.get(pk=1)
        message.chat = chat
        message.user = bob
        message.save()

    def test_create_message_success(self):
        create_message_data = CreateMessageData(
            user_id=1,
            chat_id=3,
            content="Test message",
            sent_at=timezone.make_aware(datetime(2024, 7, 19, 10, 0)),
        )

        message = MessageServices.create_message(create_message_data)

        self.assertEqual(message.user.id, 1)
        self.assertEqual(message.chat.id, 3)
        self.assertEqual(message.content, "Test message")
        self.assertEqual(
            message.sent_at, timezone.make_aware(datetime(2024, 7, 19, 10, 0))
        )

    @patch("chats.daos.MessageDao.create_message")
    def test_create_message_validation_error(self, mock_create_message):
        mock_create_message.side_effect = ValidationError("Random Error Message")

        create_message_data = CreateMessageData(
            user_id=1, chat_id=3, content="Test message", sent_at=timezone.now()
        )

        with self.assertRaises(ValidationError) as context:
            MessageServices.create_message(create_message_data)

        self.assertEqual(str(context.exception), "['Random Error Message']")
