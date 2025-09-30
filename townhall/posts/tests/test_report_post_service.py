from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from posts.types import ReportedPostData
from posts.services import ReportedPostServices
from posts.models import Post
from users.models import User
from django.forms import ValidationError
from datetime import datetime


class TestReportPostService(TestCase):
    def setUp(self):
        # Load users before posts to satisfy FK constraints
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/post_fixture.json", verbosity=0)
        self.test_post = Post.objects.get(pk=1)
        self.bob = User.objects.get(pk=1)

    def test_create_report_post_success(self):
        # Arrange
        test_data = ReportedPostData(
            user_id=self.bob.pk, post_id=self.test_post.pk, created_at=timezone.now()
        )

        # Act
        reported_post = ReportedPostServices.create_reported_post(test_data)

        # Assert
        self.assertEqual(reported_post.user_id, self.bob.pk)
        self.assertEqual(reported_post.post_id, self.test_post.pk)
        self.assertIsInstance(reported_post.created_at, datetime)

    def test_create_report_invalid_inputs(self):
        # Arrange
        test_data = ReportedPostData(
            user_id=None, post_id=self.test_post.pk, created_at=timezone.now()
        )

        # Act and Assert
        with self.assertRaises(ValidationError):
            ReportedPostServices.create_reported_post(test_data)
