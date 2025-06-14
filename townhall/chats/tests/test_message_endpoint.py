from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.core.management import call_command
from chats.models import Chat, Message
from users.models import User


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

        print(response)

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
