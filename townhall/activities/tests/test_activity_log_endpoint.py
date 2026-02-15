from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from posts.models import Post, Comment
from users.models import User


class TestActivityLogEndpoint(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Create a user, post and comment
        self.user = User.objects.create_user(
            email="test@example.com", password="password", full_name="John Doe"
        )
        self.post = Post.objects.create(user=self.user, content="Original post")
        self.comment = Comment.objects.create(
            user=self.user, post=self.post, content="Nice post!"
        )

        # Update post, comment, and user to create additional historical records
        self.post.content = "Updated and changed the post!"
        self.post.save()

        self.comment.content = "Updated and changed the comment!"
        self.comment.save()

        self.user.email = "updatedemail@example.com"
        self.user.save()

    def test_activity_log_success(self):
        # Arrange & Act
        self.client.force_authenticate(user=self.user)
        url = "/activities/"
        response = self.client.get(url, format="json")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"]

        for activity in response.data["data"]:
            assert "description" in activity

            assert "model" in activity

            assert "activity" in activity

    def test_activity_log_nonexistent_user(self):
        # Arrange & Act - no authentication
        url = "/activities/"
        response = self.client.get(url, format="json")

        # Assert - view returns 401 for unauthenticated requests
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "error" in response.data
