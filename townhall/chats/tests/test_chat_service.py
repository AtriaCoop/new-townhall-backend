from django.test import TestCase
from django.core.management import call_command
from unittest.mock import patch
from django.core.exceptions import ValidationError
from chats.models import Chat
from users.models import User
from chats.types import CreateChatData
from chats.services import ChatServices
from django.utils import timezone



# Running all tests: python3 manage.py test
# Running only chat tests: python3 manage.py test chats.tests
# Running only this specific test file:
#   python3 manage.py test chats.tests.test_chat_service


class TestChatService(TestCase):
    def setUp(self):
        call_command("loaddata", "fixtures/chat_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)

        chat = Chat.objects.get(pk=3)
        bob = User.objects.get(pk=1)
        jerome = User.objects.get(pk=2)
        chat.participants.add(bob, jerome)

    def test_get_chat_found(self):
        # Act
        chat = ChatServices.get_chat(id=3)

        # Assert
        assert chat.name == "Bob's Workers"
        assert chat.id == 3
        assert chat.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") == "2024-01-01T12:00:00Z"
        assert chat.participants.count() == 2
        assert chat.participants.filter(id=1).exists()

    @patch("chats.daos.ChatDao.get_chat")
    def test_get_chat_failed_not_found(self, mock_get_chat):
        # Arrange
        mock_get_chat.side_effect = Chat.DoesNotExist
        chat_id = 999  # Assuming this ID does not exist

        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            ChatServices.get_chat(chat_id)

        # Assert
        assert (
            str(context.exception)
            == f"['Chat with the given id: {chat_id}, does not exist.']"
        )

    def test_delete_chat_success(self):
        # Pre Assert
        chat_before = ChatServices.get_chat(id=3)
        assert chat_before.name == "Bob's Workers"

        # Arrange
        chat_id = 3

        # Act
        ChatServices.delete_chat(chat_id)

        # Assert
        with self.assertRaises(Chat.DoesNotExist):
            Chat.objects.get(id=1)

    @patch("chats.daos.ChatDao.delete_chat")
    def test_delete_chat_failed_not_found(self, mock_delete_chat):
        # Arrange
        mock_delete_chat.side_effect = Chat.DoesNotExist
        chat_id = 999  # Assuming this ID does not exist

        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            ChatServices.delete_chat(chat_id)

        # Assert
        assert (
            str(context.exception)
            == f"['Chat with the given id: {chat_id}, does not exist.']"
        )

    def test_create_chat_success(self):
        # Arrange
        create_chat_data = CreateChatData(name="Awesome Chat", participant_ids=[1])

        # Act
        chat = ChatServices.create_chat(create_chat_data)

        # Assert
        assert chat.name == "Awesome Chat"
        assert chat.created_at is not None
        assert chat.participants.count() == 1
        assert chat.participants.filter(id=1).exists()

    @patch("chats.daos.ChatDao.create_chat")
    def test_create_chat_validation_error(self, mock_create_chat):
        # Arrange
        mock_create_chat.side_effect = ValidationError("Random Error Message")
        create_chat_data = CreateChatData(
            name="Awesome Chat",
            participant_ids=[1],
        )

        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            ChatServices.create_chat(create_chat_data)

        # Assert
        assert str(context.exception) == "['Random Error Message']"
