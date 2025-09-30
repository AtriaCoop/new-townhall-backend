from django.test import TestCase
from django.core.management import call_command
from django.core.exceptions import ValidationError

from posts.models import Comment
from posts.types import UpdateCommentData
from posts.services import CommentServices

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
        self.assertEqual(updated_comment.content, "****")
        self.assertEqual(Comment.objects.get(pk=1).content, "hell")
