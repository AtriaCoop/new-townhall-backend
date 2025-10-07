from django.test import TestCase
from django.core.management import call_command
from rest_framework.test import APIClient
from urllib.parse import quote


class TestSearchUserEndpoint(TestCase):

    def setUp(self):
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)
        self.client = APIClient()
        self.url = "/user/mention/"

    def test_success(self):

        # Arrange
        test_query = "Bob The"

        # URL Encode to -> "Bob%20The"
        url_encoded_query = quote(test_query)
        url = f"{self.url}?query={url_encoded_query}"

        # Act & Assert
        response = self.client.get(url, format="json")
        results = response.data["search_results"]

        self.assertEqual(results[0]["id"], 1)
        self.assertEqual(results[0]["full_name"], "Bob The Builder")
        self.assertEqual(results[0]["email"], "bob@gmail.com")

    def test_no_match(self):
        # Arrange
        test_query = "Zzzz"

        # URL Encode query
        url_encoded_query = quote(test_query)
        url = f"{self.url}?query={url_encoded_query}"

        # Act & Assert
        response = self.client.get(url, format="json")
        results = response.data["search_results"]

        self.assertEqual(len(results), 0)

    def test_invalid_input(self):
        # Arrange
        test_query = "123 Zz"

        # URL Encode query
        url_encoded_query = quote(test_query)
        url = f"{self.url}?query={url_encoded_query}"

        # Act & Assert
        response = self.client.get(url, format="json")
        results = response.data["search_results"]

        self.assertEqual(len(results), 0)
