from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Tag, User


class TagViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(email="test@example.com", password="password")
        self.tag1 = Tag.objects.create(name="tag1")
        self.tag2 = Tag.objects.create(name="tag2")
        self.tag3 = Tag.objects.create(name="tag3")
        self.user.tags.add(self.tag1, self.tag2, self.tag3)
        self.client.force_authenticate(user=self.user)

    def test_valid_user(self):
        """Test retrieving all tags"""
        response = self.client.get("/tags/user/tags/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        tag_names = [tag["name"] for tag in response.data]
        self.assertIn("tag1", tag_names)
        self.assertIn("tag2", tag_names)
        self.assertIn("tag3", tag_names)

    def test_invalid_user(self):
        """Test retrieving tags for an unauthenticated user"""
        unauthenticated_client = APIClient()
        response = unauthenticated_client.get("/tags/user/tags/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # <-- Changed

    def test_user_with_no_tags(self):
        """Test retrieving tags for a user with no tags"""
        user_without_tags = User.objects.create(
            email="empty@example.com", password="password"
        )
        self.client.force_authenticate(user=user_without_tags)
        response = self.client.get("/tags/user/tags/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_non_integer_user_id(self):
        """Test retrieving tags with a non-integer user ID"""
        response = self.client.get("/tags/user/tags/?user_id=abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
