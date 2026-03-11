from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.core.management import call_command
from chats.models import Chat, Message
from users.models import User
from django.contrib.auth.hashers import make_password


class TestMessageEndpoint(TestCase):
    def setUp(self):
        self.client = APIClient()

        call_command("loaddata", "fixtures/chat_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/message_fixture.json", verbosity=0)

        message = Message.objects.get(pk=3)
        chat = Chat.objects.get(pk=3)
        bob = User.objects.get(pk=1)
        message.chat = chat
        message.user = bob
        message.save()

        # Set the password properly (it might be stored as plain text in fixture)
        bob.password = make_password("987password")
        bob.save()

        # Login the user to create a session
        self.client.login(username=bob.email, password="987password")

    def test_create_message_success(self):
        # Arrange
        url = "/chats/messages/"
        valid_data = {
            "user_id": 1,
            "chat_id": 3,
            "content": "Sample message",
        }

        # Act
        response = self.client.post(url, valid_data, format="json")

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"]
        assert response.data["message"] == "Message sent successfully"
        assert response.data["data"]["user_id"] == 1
        assert response.data["data"]["chat_id"] == 3
        assert response.data["data"]["content"] == "Sample message"
        assert response.data["data"]["image_content"] is None
        assert response.data["data"]["id"] is not None
        assert response.data["data"]["sent_at"] is not None

    def test_create_message_fail_invalid_data(self):
        # Arrange
        url = "/chats/messages/"
        invalid_data = {
            "sender_id": 1,
            "chat": 1,
            # no content
        }

        # Act
        response = self.client.post(url, invalid_data, format="json")

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not response.data["success"]

    def test_delete_message_success(self):
        # Arrange
        url = "/chats/messages/3/"

        # Act
        response = self.client.delete(url, format="json")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"]
        assert response.data["message"] == "Message Deleted Successfully"
        try:
            Message.objects.get(id=3)
            self.fail("Should have returned a Message or Does Not Exist Error")
        except Message.DoesNotExist:
            pass

    def test_delete_message_fail_does_not_exist(self):
        # Arrange
        url = "/chats/messages/99999/"

        # Act
        response = self.client.delete(url, format="json")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert not response.data["success"]
        assert (
            response.data["message"]
            == "['Message with the given id: 99999, does not exist.']"
        )

    def test_update_message_success(self):
        # Arrange
        url = "/chats/messages/3/"
        updated_data = {
            "content": "New updated message",
        }

        # Act
        response = self.client.patch(url, updated_data, format="json")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"]
        assert response.data["message"] == "Message updated successfully"

    def test_update_message_fail_does_not_exist(self):
        # Arrange
        url = "/chats/messages/999999999/"  # assume this message does not exist
        updated_data = {
            "content": "New updated message",
        }

        # Act
        response = self.client.patch(url, updated_data, format="json")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert not response.data["success"]
        assert (
            response.data["message"]
            == "['Message with the given id: 999999999, does not exist.']"
        )
