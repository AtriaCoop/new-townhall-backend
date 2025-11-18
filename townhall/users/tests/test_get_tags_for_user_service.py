from django.test import TestCase
from users.models import User, Tag
from users.services import UserServices
from django.core.exceptions import ValidationError


class GetTagsForUserServiceTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(email="test@example.com", password="password")
        self.tag1 = Tag.objects.create(name="tag1")
        self.tag2 = Tag.objects.create(name="tag2")
        self.tag3 = Tag.objects.create(name="tag3")
        self.tag4 = Tag.objects.create(name="tag4")
        self.user.tags.add(self.tag1, self.tag2, self.tag3, self.tag4)

    def test_valid_user(self):
        tags_qs = UserServices.get_tags_for_user(self.user.id)
        tag_names = set(tags_qs.values_list("name", flat=True))
        self.assertSetEqual(tag_names, {"tag1", "tag2", "tag3", "tag4"})

    def test_invalid_user(self):
        fake_user_id = 9999  # Assuming this ID does not exist
        # Should raise ValidationError because user does not exist
        with self.assertRaises(ValidationError):
            UserServices.get_tags_for_user(fake_user_id)

    def test_user_with_no_tags(self):
        user_without_tags = User.objects.create(
            email="empty@example.com", password="password"
        )
        tags_qs = UserServices.get_tags_for_user(user_without_tags.id)
        self.assertEqual(list(tags_qs), [])  # or assertEqual(tags_qs.count(), 0)

    def test_non_integer_user_id(self):
        with self.assertRaises((ValueError)):
            UserServices.get_tags_for_user("not-an-integer")
