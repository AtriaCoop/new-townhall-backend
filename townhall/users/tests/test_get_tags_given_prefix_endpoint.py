from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Tag


class TagViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tag1 = Tag.objects.create(name="python")
        self.tag2 = Tag.objects.create(name="pytorch")
        self.tag3 = Tag.objects.create(name="django")

    def test_returns_tags_matching_prefix(self):
        response = self.client.get("/tags/given-prefix/", {"prefix": "py"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected = [
            {"id": self.tag1.id, "name": "python"},
            {"id": self.tag2.id, "name": "pytorch"},
        ]

        self.assertEqual(response.data, expected)

    def test_case_insensitive(self):
        response = self.client.get("/tags/given-prefix/", {"prefix": "PY"})

        expected = [
            {"id": self.tag1.id, "name": "python"},
            {"id": self.tag2.id, "name": "pytorch"},
        ]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)

    def test_returns_empty_list_for_no_matches(self):
        response = self.client.get("/tags/given-prefix/", {"prefix": "zzz"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
