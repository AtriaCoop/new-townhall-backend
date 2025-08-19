from django.test import TestCase
from django.core.management import call_command
from unittest.mock import patch
from django.core.exceptions import ValidationError
from chats.models import Chat, Message
from users.models import User
from chats.types import CreateMessageData, UpdateMessageData
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

    def test_get_message_found(self):
        # Act
        message = MessageServices.get_message(id=3)

        # Assert
        assert message.id == 3
        assert message.user_id == 1
        assert message.chat_id == 3
        assert message.content == "Test message"

    @patch("chats.daos.MessageDao.get_message")
    def test_get_message_failed_not_found(self, mock_get_message):
        # Arrange
        mock_get_message.side_effect = Message.DoesNotExist
        message_id = -10  # Assuming this ID does not exist

        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            MessageServices.get_message(message_id)

        # Assert
        assert (
            str(context.exception)
            == f"['Message with the given id: {message_id}, does not exist.']"
        )

    def test_delete_message_success(self):
        # Pre Assert
        message_before = MessageServices.get_message(id=3)
        assert message_before.content == "Test message"

        # Arrange
        message_id = 3

        # Act
        MessageServices.delete_message(message_id)

        # Assert
        with self.assertRaises(Message.DoesNotExist):
            Message.objects.get(id=1)

    @patch("chats.daos.MessageDao.delete_message")
    def test_delete_message_failed_not_found(self, mock_delete_message):
        # Arrange
        mock_delete_message.side_effect = Message.DoesNotExist
        message_id = -10  # Assuming this ID does not exist

        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            MessageServices.delete_message(message_id)

        # Assert
        assert (
            str(context.exception)
            == f"['Message with the given id: {message_id}, does not exist.']"
        )

    def test_update_message_success(self):
        # Check message before update
        message_before_update = MessageServices.get_message(id=3)
        assert message_before_update.user_id == 1
        assert message_before_update.chat_id == 3
        assert message_before_update.content == "Test message"

        # Create data for updating
        update_message_data = UpdateMessageData(
            id=3, user_id=4, chat_id=21, content="Updated message"
        )

        # Update the message
        MessageServices.update_message(id=3, update_message_data=update_message_data)

        # Get the updated message and assert
        updated_message = MessageServices.get_message(id=3)

        assert updated_message.user_id == 4
        assert updated_message.chat_id == 21
        assert updated_message.content == "Updated message"

    @patch("chats.daos.MessageDao.update_message")
    def test_update_message_failed_not_found(self, mock_update_data):
        # Arrange
        mock_update_data.side_effect = Message.DoesNotExist
        message_id = -1  # Assume this message id does not exist

        update_message_data = UpdateMessageData(
            id=3, user_id=4, chat_id=21, content="Updated message"
        )

        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            MessageServices.update_message(message_id, update_message_data)

        # Assert
        assert (
            str(context.exception)
            == f"['Message with the given id: {message_id}, does not exist.']"
        )
