from rest_framework.test import APITestCase
from rest_framework import status

from posts.models import Post, Reaction
from users.models import User


class ReactionTests(APITestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            email="user1@test.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com", password="testpass123"
        )

        # Create test post
        self.post = Post.objects.create(user=self.user1, content="Test post content")

        # Set up authentication
        self.client.force_login(self.user1)

    def test_add_reaction(self):
        """Test adding a reaction to a post"""
        url = f"/post/{self.post.id}/reaction/"
        data = {"reaction_type": "love"}

        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Reaction.objects.filter(
                post=self.post, user=self.user1, reaction_type="love"
            ).exists()
        )

    def test_remove_reaction(self):
        """Test removing an existing reaction"""
        # First add a reaction
        Reaction.objects.create(post=self.post, user=self.user1, reaction_type="love")

        url = f"/post/{self.post.id}/reaction/"
        data = {"reaction_type": "love"}

        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            Reaction.objects.filter(
                post=self.post, user=self.user1, reaction_type="love"
            ).exists()
        )

    def test_invalid_reaction_type(self):
        """Test adding an invalid reaction type"""
        url = f"/post/{self.post.id}/reaction/"
        data = {"reaction_type": "not_a_valid_reaction"}

        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_multiple_users_reactions(self):
        """Test multiple users can react to the same post"""
        url = f"/post/{self.post.id}/reaction/"

        # First user reaction
        data1 = {"reaction_type": "love"}
        response1 = self.client.patch(url, data1, format="json")

        # Second user reaction
        self.client.force_login(self.user2)
        data2 = {"reaction_type": "appreciate"}
        response2 = self.client.patch(url, data2, format="json")

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(Reaction.objects.filter(post=self.post).count(), 2)

    def test_unauthenticated_user(self):
        """Test reaction from unauthenticated user"""
        self.client.logout()
        url = f"/post/{self.post.id}/reaction/"
        data = {"reaction_type": "love"}

        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
