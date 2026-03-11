from django.test import TestCase
from rest_framework.test import APIClient
from django.core.management import call_command
from users.models import User
from rest_framework import status
from django.contrib.auth.hashers import make_password


class TestReportEndpoint(TestCase):
    def setUp(self):
        self.client = APIClient()

        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/report_fixture.json", verbosity=0)

        bob = User.objects.get(pk=1)
        bob.password = make_password("987password")
        bob.save()

        self.client.login(username=bob.email, password="987password")

    def test_create_report_success(self):
        url = "/user/report/"
        valid_data = {"user_id": 1, "content": "There is a bug here. Fix it!"}

        response = self.client.post(url, valid_data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"]
        assert response.data["message"] == "Report Created Successfully"
        assert response.data["data"]["user_id"] == 1
        assert response.data["data"]["content"] == "There is a bug here. Fix it!"
        assert response.data["data"]["created_at"] is not None

    def test_create_report_invalid_data(self):
        url = "/user/report/"
        invalid_data = {
            "user_id": 1,
            # no content
        }

        response = self.client.post(url, invalid_data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_report_success(self):
        # Arrange
        url = "/user/report/1/"

        # Act
        response = self.client.get(url, format="json")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"]
        assert response.data["message"] == "Report Retrieved Successfully"
        assert response.data["report"]["user_id"] == 1
        assert response.data["report"]["content"] == "There is a bug here. Fix it!"
        assert response.data["report"]["created_at"] == "2025-11-22T12:00:00Z"

    def test_get_report_fail_service_error(self):
        # Arrange
        url = "/user/report/9999/"

        # Act
        response = self.client.get(url, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        assert not response.data["success"]
        assert (
            response.data["message"]
            == "['Report with the given id: 9999, does not exist.']"
        )
