from django.test import SimpleTestCase
from unittest.mock import patch
from types import SimpleNamespace

from posts.services import PostServices


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

    @patch("posts.services.PostDao.create_post")
    def test_create_post_masks(self, mock_create):
        # Return whatever the DAO would have saved — we only care about masking.
        mock_create.return_value = SimpleNamespace(content="damn this bug")

        class CreatePostData:
            def __init__(self, content):
                self.content = content

        post = PostServices.create_post(CreatePostData(content="damn this bug"))
        self.assertEqual(post.content, "**** this bug")

    @patch("posts.services.PostDao.update_post")
    def test_update_post_masks(self, mock_update):
        mock_update.return_value = SimpleNamespace(content="you BITCH!")

        class UpdatePostData:
            pass

        post = PostServices.update_post(1, UpdatePostData())
        self.assertEqual(post.content, "you *****!")
