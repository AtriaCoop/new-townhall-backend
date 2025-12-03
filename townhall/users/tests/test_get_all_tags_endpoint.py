from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Tag


class TagViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tag1 = Tag.objects.create(name="tag1")
        self.tag2 = Tag.objects.create(name="tag2")
        self.tag3 = Tag.objects.create(name="tag3")

    def test_get_all_tags(self):
        """Test retrieving all tags"""
        response = self.client.get("/tags/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_get_all_tags_returns_correct_data(self):
        """Test that all tags are returned with correct data"""
        response = self.client.get("/tags/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tag_names = [tag["name"] for tag in response.data]
        self.assertIn("tag1", tag_names)
        self.assertIn("tag2", tag_names)
        self.assertIn("tag3", tag_names)

    def test_get_all_tags_empty(self):
        """Test retrieving all tags when none exist"""
        Tag.objects.all().delete()
        response = self.client.get("/tags/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_get_single_tag(self):
        """Test retrieving a single tag by ID"""
        response = self.client.get(f"/tags/{self.tag1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "tag1")

    def test_create_tag(self):
        """Test creating a new tag"""
        data = {"name": "new_tag"}
        response = self.client.post("/tags/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "new_tag")
        self.assertTrue(Tag.objects.filter(name="new_tag").exists())

    def test_delete_tag(self):
        """Test deleting a tag"""
        response = self.client.delete(f"/tags/{self.tag1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=self.tag1.id).exists())
