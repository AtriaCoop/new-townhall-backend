from django.test import SimpleTestCase
from unittest.mock import patch
from types import SimpleNamespace
from django.utils import timezone
from posts.types import ReportedPostsData
from posts.services import ReportedPostsServices
from django.forms import ValidationError


class ReportPostTests(SimpleTestCase):

    @patch("posts.services.ReportedPostsServices.create_reported_post")
    def test_create_report_post_success(self, mock_create_reported_post):
        mock_create_reported_post.return_value = SimpleNamespace(
            id=1, user_id=1, post_id=1, created_at=timezone.now()
        )
        test_data = ReportedPostsData(user_id=1, post_id=1, created_at=timezone.now())
        reported_post = ReportedPostsServices.create_reported_post(test_data)

        mock_create_reported_post.assert_called_once_with(test_data)
        self.assertEqual(reported_post.id, 1)
        self.assertEqual(reported_post.user_id, 1)
        self.assertEqual(reported_post.post_id, 1)
        self.assertIsNotNone(reported_post.created_at)

    @patch("posts.services.ReportedPostsServices.create_reported_post")
    def test_create_report_post_invalid_inputs(self, mock_create_reported_post):
        mock_create_reported_post.side_effect = ValidationError(
            "Invalid user_id or post_id"
        )
        test_data = ReportedPostsData(
            user_id=None, post_id=1, created_at=timezone.now()
        )

        with self.assertRaises(ValidationError):
            ReportedPostsServices.create_reported_post(test_data)
        mock_create_reported_post.assert_called_once_with(test_data)
