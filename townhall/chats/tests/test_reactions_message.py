from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from chats.models import Chat, Message, MessageReaction
from chats.services import ReactionServices
from chats.types import ToggleMessageReactionData
from users.models import User


class TestMessageReactionService(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@test.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com", password="testpass123"
        )
        self.chat = Chat.objects.create(name="Test Chat")
        self.chat.participants.add(self.user1, self.user2)
        self.message = Message.objects.create(
            user=self.user1, chat=self.chat, content="Test message content"
        )

    def test_toggle_add_reaction(self):
        # Arrange
        reaction_data = ToggleMessageReactionData(
            user_id=self.user1.id,
            message_id=self.message.id,
            reaction_type="love",
        )

        # Act
        reaction_created, message = ReactionServices.toggle_reaction_on_message(
            reaction_data
        )

        # Assert
        self.assertTrue(reaction_created)
        self.assertEqual(message, "Added love reaction")
        self.assertTrue(
            MessageReaction.objects.filter(
                message=self.message, user=self.user1, reaction_type="love"
            ).exists()
        )

    def test_toggle_remove_reaction(self):
        # Arrange
        MessageReaction.objects.create(
            message=self.message, user=self.user1, reaction_type="love"
        )
        reaction_data = ToggleMessageReactionData(
            user_id=self.user1.id,
            message_id=self.message.id,
            reaction_type="love",
        )

        # Act
        reaction_created, message = ReactionServices.toggle_reaction_on_message(
            reaction_data
        )

        # Assert
        self.assertFalse(reaction_created)
        self.assertEqual(message, "Removed love reaction")
        self.assertFalse(
            MessageReaction.objects.filter(
                message=self.message, user=self.user1, reaction_type="love"
            ).exists()
        )

    def test_invalid_reaction_type(self):
        # Arrange
        reaction_data = ToggleMessageReactionData(
            user_id=self.user1.id,
            message_id=self.message.id,
            reaction_type="not_a_valid_reaction",
        )

        # Act
        with self.assertRaises(ValidationError):
            ReactionServices.toggle_reaction_on_message(reaction_data)

        # Assert
        self.assertFalse(MessageReaction.objects.filter(message=self.message).exists())

    def test_message_not_found(self):
        # Arrange
        reaction_data = ToggleMessageReactionData(
            user_id=self.user1.id,
            message_id=99999,
            reaction_type="love",
        )

        # Act
        with self.assertRaises(ValidationError) as context:
            ReactionServices.toggle_reaction_on_message(reaction_data)

        # Assert
        self.assertIn("Message with the given id: 99999", str(context.exception))

    def test_user_not_found(self):
        # Arrange
        reaction_data = ToggleMessageReactionData(
            user_id=99999,
            message_id=self.message.id,
            reaction_type="love",
        )

        # Act
        with self.assertRaises(ValidationError) as context:
            ReactionServices.toggle_reaction_on_message(reaction_data)

        # Assert
        self.assertIn("User with id 99999 does not exist", str(context.exception))

    def test_multiple_users_can_react(self):
        # Arrange
        user1_reaction_data = ToggleMessageReactionData(
            user_id=self.user1.id,
            message_id=self.message.id,
            reaction_type="love",
        )
        user2_reaction_data = ToggleMessageReactionData(
            user_id=self.user2.id,
            message_id=self.message.id,
            reaction_type="appreciate",
        )

        # Act
        ReactionServices.toggle_reaction_on_message(user1_reaction_data)
        ReactionServices.toggle_reaction_on_message(user2_reaction_data)

        # Assert
        self.assertEqual(
            MessageReaction.objects.filter(message=self.message).count(), 2
        )


class TestMessageReactionEndpoint(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@test.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com", password="testpass123"
        )
        self.chat = Chat.objects.create(name="Test Chat")
        self.chat.participants.add(self.user1, self.user2)
        self.message = Message.objects.create(
            user=self.user1, chat=self.chat, content="Test message content"
        )
        self.url = f"/chats/messages/{self.message.id}/reaction/"
        self.client.force_login(self.user1)

    def test_add_reaction(self):
        # Arrange
        data = {"reaction_type": "love"}

        # Act
        response = self.client.patch(self.url, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Added love reaction")
        self.assertIn("love", response.data["reactions"])
        self.assertTrue(
            MessageReaction.objects.filter(
                message=self.message, user=self.user1, reaction_type="love"
            ).exists()
        )

    def test_remove_reaction(self):
        # Arrange
        MessageReaction.objects.create(
            message=self.message, user=self.user1, reaction_type="love"
        )
        data = {"reaction_type": "love"}

        # Act
        response = self.client.patch(self.url, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Removed love reaction")
        self.assertNotIn("love", response.data["reactions"])
        self.assertFalse(
            MessageReaction.objects.filter(
                message=self.message, user=self.user1, reaction_type="love"
            ).exists()
        )

    def test_invalid_reaction_type(self):
        # Arrange
        data = {"reaction_type": "not_a_valid_reaction"}

        # Act
        response = self.client.patch(self.url, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_reaction_type(self):
        # Arrange
        data = {}

        # Act
        response = self.client.patch(self.url, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Reaction type is required")

    def test_message_not_found(self):
        # Arrange
        url = "/chats/messages/99999/reaction/"
        data = {"reaction_type": "love"}

        # Act
        response = self.client.patch(url, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_multiple_users_reactions(self):
        # Arrange
        data1 = {"reaction_type": "love"}
        data2 = {"reaction_type": "appreciate"}

        # Act
        response1 = self.client.patch(self.url, data1, format="json")
        self.client.force_login(self.user2)
        response2 = self.client.patch(self.url, data2, format="json")

        # Assert
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(
            MessageReaction.objects.filter(message=self.message).count(), 2
        )
        self.assertIn("love", response1.data["reactions"])
        self.assertIn("appreciate", response2.data["reactions"])

    def test_unauthenticated_user(self):
        # Arrange
        data = {"reaction_type": "love"}
        self.client.logout()

        # Act
        response = self.client.patch(self.url, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
