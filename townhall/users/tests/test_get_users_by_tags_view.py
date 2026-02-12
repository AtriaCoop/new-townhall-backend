from django.forms import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from users.models import User, Tag


class TagViewSetTests(TestCase):
    def setUp(self):
        # Create some tags
        self.tag_python = Tag.objects.create(name="Python")
        self.tag_django = Tag.objects.create(name="Django")
        self.tag_react = Tag.objects.create(name="React")
        self.tag_angular = Tag.objects.create(name="Angular")
        self.tag_svelte = Tag.objects.create(name="Svelte")
        self.tag_vue = Tag.objects.create(name="Vue")

        # Create some users
        self.user1 = User.objects.create(email="user1@test.com")
        self.user1.tags.add(
            self.tag_python, self.tag_django, self.tag_react, self.tag_angular
        )

        self.user2 = User.objects.create(email="user2@test.com")
        self.user2.tags.add(self.tag_react, self.tag_svelte)

        self.user3 = User.objects.create(email="user3@test.com")
        self.user3.tags.add(self.tag_python, self.tag_angular)

        self.user4 = User.objects.create(email="user4@test.com")

        self.user5 = User.objects.create(email="user5@test.com")
        self.user5.tags.add(self.tag_svelte)

    def test_single_tag_returns_correct_users(self):
        url = reverse("users-get-users-by-tags")

        response = self.client.get(url, {"tags": ["Python"]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {user["id"] for user in response.data}

        self.assertSetEqual(returned_ids, {self.user1.id, self.user3.id})

    def test_multiple_tags_returns_correct_users(self):
        url = reverse("users-get-users-by-tags")

        response = self.client.get(url, {"tags": ["Python", "React"]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {user["id"] for user in response.data}

        self.assertSetEqual(returned_ids, {self.user1.id, self.user2.id, self.user3.id})

    def test_no_matching_users(self):
        url = reverse("users-get-users-by-tags")

        response = self.client.get(url, {"tags": ["Vue"]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {user["id"] for user in response.data}

        self.assertSetEqual(returned_ids, set())

    def test_no_tags_provided(self):
        url = reverse("users-get-users-by-tags")

        with self.assertRaises(ValidationError) as context:
            self.client.get(url, {"tags": []})

        self.assertIn("At least one tag name must be provided", str(context.exception))
