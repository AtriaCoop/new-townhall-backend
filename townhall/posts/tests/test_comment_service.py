from django.test import TestCase
from django.core.management import call_command
from django.core.exceptions import ValidationError

from posts.models import Comment
from posts.types import UpdateCommentData
from posts.services import CommentServices
from users.models import User

# Running all tests: python3 manage.py test
# Running only post tests: python3 manage.py test posts.tests
# Running only this specific test file:
# python3 manage.py test posts.tests.test_comment_service


class TestCommentService(TestCase):
    def setUp(self):
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/post_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/comment_fixture.json", verbosity=0)

    def test_update_comment_success(self):
        # Arrange
        comment = Comment.objects.get(pk=1)
        update_comment_data = UpdateCommentData(content="This is an update")

        # Act
        updated_comment = CommentServices.update_comment(
            comment.id, update_comment_data
        )

        # Assert
        self.assertEqual(updated_comment.content, "This is an update")
        self.assertEqual(Comment.objects.get(pk=1).content, "This is an update")

    def test_update_comment_not_found(self):
        # Arrange
        update_data = UpdateCommentData(content="This is a failed update")
        non_existent_id = 999

        # Act and Assert
        with self.assertRaises(ValidationError):
            CommentServices.update_comment(non_existent_id, update_data)

    def test_update_comment_profanity(self):
        # Arrange
        comment = Comment.objects.get(pk=1)
        update_comment_data = UpdateCommentData(content="hell")

        # Act
        updated_comment = CommentServices.update_comment(
            comment.id, update_comment_data
        )

        # Assert
        # Service returns RAW content
        self.assertEqual(updated_comment.content, "hell")

        # DB stores RAW content
        self.assertEqual(Comment.objects.get(pk=1).content, "hell")

    def test_like_comment_success(self):
        comment = Comment.objects.get(pk=1)
        other_user = User.objects.get(pk=2)

        liked, likes = CommentServices.like_comment(comment.id, other_user.id)

        self.assertTrue(liked)
        self.assertEqual(likes, 1)
        comment.refresh_from_db()
        self.assertEqual(comment.likes, 1)
        self.assertTrue(comment.liked_by.filter(pk=other_user.pk).exists())

    def test_unlike_comment_success(self):
        comment = Comment.objects.get(pk=1)
        other_user = User.objects.get(pk=2)
        comment.liked_by.add(other_user)
        comment.likes = 1
        comment.save()

        liked, likes = CommentServices.like_comment(comment.id, other_user.id)

        self.assertFalse(liked)
        self.assertEqual(likes, 0)
        comment.refresh_from_db()
        self.assertEqual(comment.likes, 0)
        self.assertFalse(comment.liked_by.filter(pk=other_user.pk).exists())

    def test_like_comment_not_found(self):
        with self.assertRaises(ValidationError):
            CommentServices.like_comment(9999, User.objects.get(pk=2).id)
