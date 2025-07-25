from django.test import TestCase
from django.core.management import call_command
from unittest.mock import patch
from django.core.exceptions import ValidationError
from chats.models import Chat
from users.models import User
from chats.types import CreateChatData
from chats.services import ChatServices


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
        chat = ChatServices.get_or_create_chat(create_chat_data)

        # Assert
        assert chat[0].name == "Awesome Chat"
        assert chat[0].created_at is not None
        assert chat[0].participants.count() == 1
        assert chat[0].participants.filter(id=1).exists()

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
            ChatServices.get_or_create_chat(create_chat_data)

        # Assert
        assert str(context.exception) == "['Random Error Message']"

    def test_get_chat_all_found(self):
        # Act
        chats = ChatServices.get_chat_all()

        # Assert
        self.assertTrue(chats.exists(), "some chats should exist for now.")
        chat_ids = [chat.id for chat in chats]
        self.assertIn(3, chat_ids)

    def test_get_chat_all_not_found(self):
        # Arrange
        Chat.objects.all().delete()

        # Act and Assert
        with self.assertRaises(ValidationError) as noChats:
            ChatServices.get_chat_all()

        # Assert
        self.assertEqual(str(noChats.exception), "['No chats were found.']")

    def test_add_user_success(self):
        # Arrange
        chat_id = 3
        new_user = User.objects.create(
            id=5, email="newuser5@example.com", full_name="newuser"
        )
        # Act
        ChatServices.add_user(chat_id=chat_id, user_id=new_user.id)
        # Assert
        chat = Chat.objects.get(id=chat_id)
        self.assertTrue(
            chat.participants.filter(id=new_user.id).exists(),
            "User should be added to chat participants.",
        )

    def test_add_user_failure(self):
        # User already in chat
        chat_id = 3
        existing_user_id = 1
        with self.assertRaises(ValidationError) as context:
            ChatServices.add_user(chat_id=chat_id, user_id=existing_user_id)
        self.assertIn("already a participant", str(context.exception))

        # User does not exist
        non_existent_user_id = 9999
        with self.assertRaises(ValidationError) as context:
            ChatServices.add_user(chat_id=chat_id, user_id=non_existent_user_id)
        self.assertIn("does not exist", str(context.exception))

        # Chat does not exist
        non_existent_chat_id = 9999
        with self.assertRaises(ValidationError) as context:
            ChatServices.add_user(chat_id=non_existent_chat_id, user_id=1)
        self.assertIn("does not exist", str(context.exception))

    def test_update_chat_participants_success(self):
        # Arrange
        chat_id = 3
        new_participant_ids = [1, 2, 3]

        # Act
        updated_chat = ChatServices.update_chat_participants(
            chat_id, new_participant_ids
        )

        # Assert
        self.assertEqual(updated_chat.id, chat_id)
        self.assertEqual(updated_chat.participants.count(), 3)
        self.assertEqual(
            set(updated_chat.participants.values_list("id", flat=True)), {1, 2, 3}
        )

    def test_update_chat_not_found(self):
        # Arrange
        chat_id = 999  # Assumed non-existent chat ID
        new_participant_ids = [1, 2]

        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            ChatServices.update_chat_participants(chat_id, new_participant_ids)

        # Assert
        self.assertIn("Chat with id 999 does not exist", str(context.exception))

    def test_update_chat_less_than_two_people(self):
        # Arrange
        chat_id = 3
        new_participant_ids = [1]

        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            ChatServices.update_chat_participants(chat_id, new_participant_ids)

        # Assert
        self.assertIn(
            "Chat must have at least two participants", str(context.exception)
        )
