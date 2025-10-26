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
        url = f"/activities/?user_id={self.user.id}"
        response = self.client.get(url, format="json")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"]

        for activity in response.data["data"]:
            assert "description" in activity

            assert "model" in activity

            assert "activity" in activity

    def test_activity_log_nonexistent_user(self):

        # Arrange & Act
        url = "/activities/?user_id=9999"
        response = self.client.get(url, format="json")

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not response.data.get("success", False)

    def test_activity_log_nonsensical_user_id(self):

        # Arrange & Act
        url = "/activities/?user_id=ABC"
        response = self.client.get(url, format="json")

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not response.data.get("success", False)

    def test_activity_log_no_user_id(self):

        # Arrange & Act
        url = "/activities/?user_id="
        response = self.client.get(url, format="json")

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not response.data.get("success", False)
