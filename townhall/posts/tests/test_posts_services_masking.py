from django.test import SimpleTestCase
from unittest.mock import patch
from types import SimpleNamespace

from django.utils import timezone

from posts.services import PostServices
from posts.types import CreatePostData, UpdatePostData


class PostServicesMaskingTests(SimpleTestCase):
    @patch("posts.services.PostDao.get_all_posts")
    def test_get_all_posts_masks(self, mock_get_all):
        mock_get_all.return_value = [SimpleNamespace(content="shit happens")]
        posts = PostServices.get_all_posts()
        self.assertEqual(posts[0].content, "**** happens")

    @patch("posts.services.PostDao.get_post")
    def test_get_post_masks(self, mock_get):
        mock_get.return_value = SimpleNamespace(content="you asshole")
        post = PostServices.get_post(1)
        self.assertEqual(post.content, "you *******")

    @patch("posts.services.User.objects.get")
    @patch("posts.services.PostDao.create_post")
    def test_create_post_masks(self, mock_create, mock_user_get):
        # Return whatever the DAO would have saved — we only care about masking.
        mock_create.return_value = SimpleNamespace(content="damn this bug")
        mock_user_get.return_value = SimpleNamespace(is_staff=False)

        post_data = CreatePostData(
            content="damn this bug", user_id=1, created_at=timezone.now(), pinned=False
        )

        post = PostServices.create_post(post_data)
        self.assertEqual(post.content, "**** this bug")

    @patch("posts.services.User.objects.get")
    @patch("posts.services.PostDao.update_post")
    def test_update_post_masks(self, mock_update, mock_user_get):
        mock_update.return_value = SimpleNamespace(content="you BITCH!")
        mock_user_get.return_value = SimpleNamespace(is_staff=False)
        update_data = UpdatePostData(content="you BITCH!", user_id=1)

        post = PostServices.update_post(1, update_data)
        self.assertEqual(post.content, "you *****!")
