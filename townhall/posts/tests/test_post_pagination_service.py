from django.test import TestCase
from django.core.management import call_command

from posts.services import PostServices
from posts.models import Post


class TestPostPaginationService(TestCase):
    def setUp(self):
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/post_fixture.json", verbosity=0)

    def test_posts_with_pagination_success(self):
        # Arrange
        page = 1
        limit = 10

        # Act
        posts, total_pages = PostServices.get_all_posts(page=page, limit=limit)

        # Assert
        self.assertEqual(len(posts), 10)
        self.assertTrue(posts[0].created_at > posts[-1].created_at)

    def test_posts_with_pagination_defaults(self):
        # Act
        posts, total_pages = PostServices.get_all_posts()

        # Assert
        self.assertEqual(len(posts), 10)
        self.assertTrue(posts[0].created_at > posts[-1].created_at)

    def test_posts_with_pagination_second_page(self):
        # Arrange
        page = 2
        limit = 8

        # Act
        posts, total_pages = PostServices.get_all_posts(page=page, limit=limit)

        # Assert
        self.assertEqual(len(posts), 8)
        self.assertTrue(posts[0].created_at > posts[-1].created_at)

    def test_posts_with_pagination_invalid_page(self):
        # Arrange
        page = -1
        limit = 5

        # Act
        posts, total_pages = PostServices.get_all_posts(page=page, limit=limit)

        # Assert
        self.assertEqual(len(posts), 5)
        self.assertTrue(posts[0].created_at > posts[-1].created_at)

    def test_posts_with_pagination_invalid_limit(self):
        # Arrange
        page = 1
        limit = 0

        # Act
        posts, total_pages = PostServices.get_all_posts(page=page, limit=limit)

        # Assert
        self.assertEqual(len(posts), 1)

    def test_posts_with_pagination_limit_exceed(self):
        # Arrange
        page = 1
        limit = 1000
        total_posts = Post.objects.count()

        # Act
        posts, total_pages = PostServices.get_all_posts(page=page, limit=limit)

        # Assert
        self.assertEqual(len(posts), total_posts)

    def test_posts_with_pagination_empty(self):
        # Arrange
        Post.objects.all().delete()

        # Act
        posts, total_pages = PostServices.get_all_posts(page=1, limit=10)

        # Assert
        self.assertEqual(len(posts), 0)

    def test_posts_with_pagination_page_beyond_posts(self):
        # Arrange
        page = 1000
        limit = 5

        # Act
        posts, total_pages = PostServices.get_all_posts(page=page, limit=limit)

        # Assert
        self.assertEqual(len(posts), 0)

    def test_posts_with_pagination_total_pages(self):
        # Arrange
        page = 1
        limit = 10
        total_posts = Post.objects.count()
        act_total_pages = (total_posts + limit - 1) // limit

        # Act
        posts, total_pages = PostServices.get_all_posts(page=page, limit=limit)

        # Assert
        print("PAGES, ", total_pages)
        self.assertEqual(total_pages, act_total_pages)
        self.assertEqual(len(posts), 10)
