from django.test import SimpleTestCase
from unittest.mock import patch
from types import SimpleNamespace
from django.utils import timezone
from posts.types import ReportedPostData
from posts.services import ReportedPostServices
from django.forms import ValidationError


class ReportPostTests(SimpleTestCase):

    @patch("posts.services.ReportedPostServices.create_reported_post")
    def test_create_report_post_success(self, mock_create_reported_post):
        mock_create_reported_post.return_value = SimpleNamespace(
            id=1, user_id=1, post_id=1, created_at=timezone.now()
        )
        test_data = ReportedPostData(user_id=1, post_id=1, created_at=timezone.now())
        reported_post = ReportedPostServices.create_reported_post(test_data)

        mock_create_reported_post.assert_called_once_with(test_data)
        self.assertEqual(reported_post.id, 1)
        self.assertEqual(reported_post.user_id, 1)
        self.assertEqual(reported_post.post_id, 1)
        self.assertIsNotNone(reported_post.created_at)

    @patch("posts.services.ReportedPostServices.create_reported_post")
    def test_create_report_post_invalid_inputs(self, mock_create_reported_post):
        mock_create_reported_post.side_effect = ValidationError(
            "Invalid user_id or post_id"
        )
        test_data = ReportedPostData(user_id=None, post_id=1, created_at=timezone.now())

        with self.assertRaises(ValidationError):
            ReportedPostServices.create_reported_post(test_data)
        mock_create_reported_post.assert_called_once_with(test_data)
