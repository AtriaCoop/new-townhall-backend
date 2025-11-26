from django.test import TestCase
from users.models import User, Tag
from users.services import UserServices


class GetUsersByTagsTests(TestCase):
    def setUp(self):
        # Create some tags
        self.tag_python = Tag.objects.create(name="Python")
        self.tag_django = Tag.objects.create(name="Django")
        self.tag_react = Tag.objects.create(name="React")

        # Create some users
        self.user1 = User.objects.create(email="user1@test.com")
        self.user1.tags.add(self.tag_python, self.tag_django)

        self.user2 = User.objects.create(email="user2@test.com")
        self.user2.tags.add(self.tag_react)

        self.user3 = User.objects.create(email="user3@test.com")
        self.user3.tags.add(self.tag_python)

    def test_single_tag(self):
        users = UserServices.get_users_by_tags(["Python"])
        self.assertEqual(set(users), {self.user1, self.user3})

    def test_multiple_tags(self):
        users = UserServices.get_users_by_tags(["Python", "Django"])
        self.assertIn(self.user1, users)
        self.assertIn(self.user3, users)
        self.assertNotIn(self.user2, users)

    def test_no_matching_tags(self):
        users = UserServices.get_users_by_tags(["Nonexistent"])
        self.assertEqual(users.count(), 0)
