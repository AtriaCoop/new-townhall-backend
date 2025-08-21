from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from django.core.exceptions import ValidationError


class UpdateUserEndpointTagsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_id = 1
        self.url = f"/user/{self.user_id}/"

    @patch("users.views.UserServices.update_user")
    def test_update_user_with_receive_emails_success(self, mock_update_user):
        "Test succesful user update with receive_emails"
        mock_update_user.return_value = None

        data = {"receive_emails": False}
        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "User Updated Successfully")

        mock_update_user.assert_called_once()
        call_args = mock_update_user.call_args[0][0]  # Get the UpdateUserData object
        self.assertEqual(call_args.receive_emails, False)

    @patch("users.views.UserServices.update_user")
    def test_update_user_with_invalid_receive_email(self, mock_update_user):
        "Test for a fail with invalid receive_emails"
        mock_update_user.return_value = None

        data = {"receive_emails": "Hello"}
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("users.views.UserServices.update_user")
    def test_update_user_with_tags_success(self, mock_update_user):
        """Test successful user update with tags"""
        mock_update_user.return_value = None

        data = {"tags": ["python", "django", "backend"]}
        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "User Updated Successfully")

        # Verify tags are passed correctly to service
        mock_update_user.assert_called_once()
        call_args = mock_update_user.call_args[0][0]  # Get the UpdateUserData object
        self.assertEqual(call_args.tags, ["python", "django", "backend"])

    @patch("users.views.UserServices.update_user")
    def test_update_user_with_empty_tags(self, mock_update_user):
        """Test user update with empty tags list"""
        mock_update_user.return_value = None

        data = {"tags": []}
        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        call_args = mock_update_user.call_args[0][0]
        self.assertEqual(call_args.tags, [])

    @patch("users.views.UserServices.update_user")
    def test_update_user_without_tags_field(self, mock_update_user):
        """Test user update without tags field (should default to empty list)"""
        mock_update_user.return_value = None

        data = {"full_name": "John Doe"}  # Other field to pass validation
        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        call_args = mock_update_user.call_args[0][0]
        self.assertEqual(call_args.tags, [])

    def test_update_user_with_invalid_tags_format(self):
        """Test user update with invalid tags format (not a list)"""
        data = {"tags": "python,django,backend"}  # String instead of list
        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tags", response.data)

    @patch("users.views.UserServices.update_user")
    def test_update_user_with_non_string_tags(self, mock_update_user):
        mock_update_user.return_value = None
        data = {"tags": ["python", 123, "django"]}  # Contains integer
        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tags", response.data)

    @patch("users.views.UserServices.update_user")
    def test_update_user_service_validation_error(self, mock_update_user):
        """Test handling of ValidationError from UserServices (e.g., user not found)"""
        mock_update_user.side_effect = ValidationError("User not found")

        data = {"tags": ["test-tag"]}
        response = self.client.patch(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "User not found")

    def test_update_user_tags_only_no_other_fields(self):
        """Test updating only tags field passes validation"""
        with patch("users.views.UserServices.update_user") as mock_update_user:
            mock_update_user.return_value = None

            data = {"tags": ["solo-tag"]}
            response = self.client.patch(self.url, data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            call_args = mock_update_user.call_args[0][0]
            self.assertEqual(call_args.tags, ["solo-tag"])
