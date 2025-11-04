from django.test import TestCase
from unittest.mock import patch
from types import SimpleNamespace
from django.utils import timezone
from rest_framework.test import APIClient
from posts.services import PostServices
from posts.types import CreatePostData, UpdatePostData
from users.models import User
from posts.models import Post


class PostPinnedTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create(email="admin@example.com", is_staff=True)
        self.regular = User.objects.create(email="user@example.com", is_staff=False)
        self.other = User.objects.create(email="other@example.com", is_staff=False)
        self.other_post = Post.objects.create(
            content="Other user's post",
            user=self.other,
            created_at=timezone.now(),
            pinned=False,
        )

        self.client = APIClient()

    @patch("posts.services.PostDao.create_post")
    def test_create_pinned_post_by_admin(self, mock_create):
        # Mock DAO return
        mock_create.return_value = SimpleNamespace(content="Hello", pinned=True)

        post_data = CreatePostData(
            content="Hello",
            user_id=self.admin.id,
            created_at=timezone.now(),
            pinned=True,
        )

        post = PostServices.create_post(post_data)
        self.assertTrue(post.pinned)

    @patch("posts.services.PostDao.update_post")
    @patch("posts.services.User.objects.get")
    def test_update_post_to_pinned_by_admin(self, mock_user_get, mock_update):
        mock_user_get.return_value = SimpleNamespace(is_staff=True)
        mock_update.return_value = SimpleNamespace(content="Update", pinned=True)

        update_data = UpdatePostData(
            content="Update", user_id=self.admin.id, pinned=True
        )

        post = PostServices.update_post(1, update_data)
        self.assertTrue(post.pinned)

    @patch("posts.services.PostDao.update_post")
    @patch("posts.services.User.objects.get")
    def test_update_post_to_unpinned_by_admin(self, mock_user_get, mock_update):
        mock_user_get.return_value = SimpleNamespace(is_staff=True)
        mock_update.return_value = SimpleNamespace(content="Update", pinned=False)

        update_data = UpdatePostData(
            content="Update", user_id=self.admin.id, pinned=False
        )

        post = PostServices.update_post(1, update_data)
        self.assertFalse(post.pinned)

    @patch("posts.services.User.objects.get")
    def test_non_admin_cannot_create_pinned(self, mock_user_get):
        mock_user_get.return_value = SimpleNamespace(is_staff=False)
        post_data = CreatePostData(
            content="Test",
            user_id=self.regular.id,
            created_at=timezone.now(),
            pinned=True,
        )

        from django.core.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            PostServices.create_post(post_data)

    @patch("posts.services.User.objects.get")
    def test_non_admin_cannot_pin(self, mock_user_get):
        mock_user_get.return_value = SimpleNamespace(is_staff=False)
        update_data = UpdatePostData(
            content="Update", user_id=self.regular.id, pinned=True
        )

        from django.core.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            PostServices.update_post(1, update_data)

    @patch("posts.services.User.objects.get")
    def test_non_admin_cannot_unpin(self, mock_user_get):
        mock_user_get.return_value = SimpleNamespace(is_staff=False)
        update_data = UpdatePostData(
            content="Update", user_id=self.regular.id, pinned=False
        )

        from django.core.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            PostServices.update_post(1, update_data)

    @patch("posts.services.User.objects.get")
    @patch("posts.services.PostDao.update_post")
    def test_admin_can_pin_others_post(self, mock_update, mock_user_get):
        mock_user_get.return_value = SimpleNamespace(is_staff=True, id=999)
        mock_update.return_value = SimpleNamespace(content="Some content", pinned=True)

        update_data = UpdatePostData(
            content=None,
            image=None,
            pinned=True,
            user_id=123,
        )

        post = PostServices.update_post(1, update_data)
        self.assertTrue(post.pinned)

    def test_user_cannot_update_others_content_or_image(self):
        self.client.force_authenticate(user=self.regular)

        response = self.client.patch(
            f"/post/{self.other_post.id}/",
            {"content": "Illegal edit", "image": None},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.other_post.refresh_from_db()
        self.assertEqual(self.other_post.content, "Other user's post")
