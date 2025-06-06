from django.test import TestCase
from django.core.management import call_command
from unittest.mock import patch
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient
from chats.models import Chat
from users.models import User

# Running all tests: python3 manage.py test
# Running only chat tests: python3 manage.py test chats.tests
# Running only this specific test file:
#   python3 manage.py test chats.tests.test_chat_endpoint


class TestChatEndpoint(TestCase):
    def setUp(self):
        self.client = APIClient()

        call_command("loaddata", "fixtures/chat_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)

        chat = Chat.objects.get(pk=3)
        bob = User.objects.get(pk=1)
        jerome = User.objects.get(pk=2)
        chat.participants.add(bob, jerome)

    def test_get_chat_success(self):
        # Arrange
        url = "/chats/3/"

        # Act
        response = self.client.get(url, format="json")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"]
        assert response.data["message"] == "Chat Retreived Successfully"
        assert response.data["data"]["name"] == "Bob's Workers"
        assert response.data["data"]["created_at"] == "2024-01-01T12:00:00Z"
        assert response.data["data"]["id"] == 3
        assert response.data["data"]["participants"][0]["id"] == 1
        assert response.data["data"]["participants"][1]["id"] == 2

    def test_get_chat_fail_service_error(self):
        # Arrange
        url = "/chats/99999999/"

        # Act
        response = self.client.get(url, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        assert not response.data["success"]
        assert (
            response.data["message"]
            == "['Chat with the given id: 99999999, does not exist.']"
        )

    def test_delete_chat_success(self):
        # Arrange
        url = "/chats/3/"

        # Act
        response = self.client.delete(url, format="json")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"]
        assert response.data["message"] == "Chat Deleted Successfully"
        try:
            Chat.objects.get(id=3)
            self.fail("Should have returned a Chat Does Not Exist Error")
        except Chat.DoesNotExist:
            pass

    def test_delete_chat_fail_does_not_exist(self):
        # Arrange
        url = "/chats/99999999/"

        # Act
        response = self.client.delete(url, format="json")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert not response.data["success"]
        assert (
            response.data["message"]
            == "['Chat with the given id: 99999999, does not exist.']"
        )

    def test_create_chat_success(self):
        # Arrange
        url = "/chats/"
        valid_data = {
            "name": "The Avengers",
            "participants": [1, 2],
        }

        # Act
        response = self.client.post(url, valid_data, format="json")

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"]
        assert response.data["message"] == "Chat Created Successfully"
        assert response.data["data"]["name"] == "The Avengers"
        assert response.data["data"]["created_at"] is not None
        assert response.data["data"]["id"] is not None
        assert response.data["data"]["participants"][0]["id"] == 1
        assert response.data["data"]["participants"][1]["id"] == 2

    def test_create_chat_fail_invalid_data(self):
        # Arrange
        url = "/chats/"
        invalid_data = {
            "name": "The Avengers",
            # doesn't have participants
        }

        # Act
        response = self.client.post(url, invalid_data, format="json")

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not response.data["success"]

    @patch("chats.services.ChatServices.get_or_create_chat")
    def test_create_chat_fail_service_error(self, mock_create_chat):
        # Arrange
        mock_create_chat.side_effect = ValidationError("random message")
        url = "/chats/"
        valid_data = {
            "name": "The Avengers",
            "participants": [1, 2],
        }

        # Act
        response = self.client.post(url, valid_data, format="json")

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not response.data["success"]
        assert response.data["message"] == "['random message']"
