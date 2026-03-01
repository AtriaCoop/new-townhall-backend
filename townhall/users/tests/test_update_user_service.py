from django.test import TestCase
from users.models import User, Tag
from users.services import UserServices
from users.types import UpdateUserData


class UpdateUserTagsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@example.com", password="password")
        self.tag1 = Tag.objects.create(name="tag1")
        self.tag2 = Tag.objects.create(name="tag2")
        self.tag3 = Tag.objects.create(name="tag3")
        self.tag4 = Tag.objects.create(name="tag4")
        self.user.receive_emails = True
        self.user.save()
        self.user.tags.add(self.tag1)

    def test_update_user_tags_with_receive_email(self):
        update_data = UpdateUserData(id=self.user.id, receive_emails=False)
        UserServices.update_user(update_data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.receive_emails, False)

    def test_update_user_tags_with_nonexistent_tags(self):
        update_data = UpdateUserData(
            id=self.user.id, tags=["nonexistent_tag_1", "nonexistent_tag_2"]
        )
        # Should NOT raise ValidationError, and tags should remain unchanged
        UserServices.update_user(update_data)
        self.user.refresh_from_db()
        self.assertSetEqual(set(self.user.tags.all()), set())

    def test_update_user_tags_with_nonexistent_user(self):
        update_data = UpdateUserData(
            id=9999, tags=["any_tag"]  # Assuming this ID does not exist
        )
        # Should raise ValidationError because user does not exist
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            UserServices.update_user(update_data)

    def test_update_user_tags_with_empty_tags(self):
        update_data = UpdateUserData(id=self.user.id, tags=[])
        UserServices.update_user(update_data)
        self.user.refresh_from_db()
        self.assertSetEqual(set(self.user.tags.all()), set())

    def test_update_user_tags_with_existing_user_and_duplicate_tag(self):
        update_data = UpdateUserData(id=self.user.id, tags=["tag1"])
        UserServices.update_user(update_data)
        self.user.refresh_from_db()
        self.assertSetEqual(set(self.user.tags.all()), {self.tag1})

    def test_update_user_tags_with_existing_user_a_duplicate_tag_and_a_new_tag(self):
        update_data = UpdateUserData(id=self.user.id, tags=["tag1", "tag2"])
        UserServices.update_user(update_data)
        self.user.refresh_from_db()
        self.assertSetEqual(set(self.user.tags.all()), {self.tag1, self.tag2})

    def test_update_user_tags_with_existing_user_and_new_tags(self):
        update_data = UpdateUserData(
            id=self.user.id, tags=["tag2", "tag2", "tag3", "tag4"]
        )
        UserServices.update_user(update_data)
        self.user.refresh_from_db()
        self.assertSetEqual(
            set(self.user.tags.all()), {self.tag2, self.tag3, self.tag4}
        )

    def test_verify_user(self):
        # assert that the user is not verified first.
        self.assertEqual(self.user.is_verified, False)

        UserServices.verify_user(user_id=self.user.id)
        self.user.refresh_from_db()

        self.assertEqual(self.user.is_verified, True)
