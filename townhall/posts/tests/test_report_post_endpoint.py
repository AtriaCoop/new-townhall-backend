from django.test import TestCase
from rest_framework.test import APIClient
from django.core.management import call_command
from posts.models import Post
from users.models import User


class ReportPostEndpointTests(TestCase):

    def setUp(self):
        # Load users before posts to satisfy FK constraints
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/post_fixture.json", verbosity=0)
        self.client = APIClient()
        self.test_user = User.objects.get(pk=1)
        self.test_post = Post.objects.get(pk=1)
        self.url = f"/post/{self.test_post.pk}/report"

    def test_report_post_endpoint_success(self):

        # Arrange
        test_data = {
            "post_id": self.test_post.pk,
            "user_id": self.test_user.pk,
        }

        # Act
        response = self.client.post(self.url, test_data, format="json")

        # Assert
        self.assertEqual(response.status_code, 201)
        self.assertIn("reported_post", response.json())

        data = response.json()
        reported_post = data["reported_post"]

        self.assertEqual(reported_post["user"]["id"], self.test_user.pk)
        self.assertEqual(reported_post["post"]["id"], self.test_post.pk)

    def test_report_post_endpoint_missing_user_id(self):

        # Arrange
        test_data = {"post_id": self.test_post.pk}

        # Act and Assert
        response = self.client.post(self.url, test_data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_report_post_endpoint_invalid_post(self):

        # simulate when post_id is non existent in DB
        test_url = "/post/99999/report"

        test_data = {
            "post_id": 99999,
            "user_id": self.test_user.pk,
        }

        # Act and Assert
        response = self.client.post(test_url, test_data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_report_post_endpoint_nonsensical_post_id(self):

        # Arrange
        test_data = {"post_id": "lol", "user_id": self.test_user.pk}

        # Act and Assert
        response = self.client.post(self.url, test_data, format="json")
        self.assertEqual(response.status_code, 400)
