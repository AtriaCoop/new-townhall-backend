from django.test import TestCase
from rest_framework.test import APIClient
from django.core.management import call_command
from posts.models import Comment
from users.models import User

# Running all tests: python3 manage.py test
# Running only post tests: python3 manage.py test posts.tests
# Running only this specific test file:
# python3 manage.py test posts.tests.test_comment_endpoint


class CommentEndpointTests(TestCase):
    def setUp(self):
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/post_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/comment_fixture.json", verbosity=0)
        self.client = APIClient()
        self.author = User.objects.get(pk=1)
        self.other_user = User.objects.get(pk=2)
        self.comment = Comment.objects.get(pk=1)
        self.url = f"/comment/{self.comment.pk}/"

    def test_update_comment_success(self):
        # Arrange
        self.client.force_authenticate(user=self.author)
        payload = {"content": "Updated via endpoint"}

        # Act
        response = self.client.patch(self.url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Updated via endpoint")

    def test_update_comment_unauthenticated(self):
        # Arrange
        payload = {"content": "Try update"}

        # Act
        response = self.client.patch(self.url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, 401)

    def test_update_other_person_comment(self):
        # Arrange
        self.client.force_authenticate(user=self.other_user)
        payload = {"content": "I will update somebody else's comment"}

        # Act
        response = self.client.patch(self.url, payload, format="json")

        # Assert
        self.assertEqual(response.status_code, 403)

    def test_update_comment_not_found(self):
        # Arrange
        self.client.force_authenticate(user=self.author)

        # Act
        response = self.client.patch("/comment/9999/", {"content": "x"}, format="json")

        # Assert
        self.assertEqual(response.status_code, 404)
