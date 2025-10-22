from django.test import TestCase
from posts.models import Post, Comment
from users.models import User
from activities.services import ActivityServices
from django.forms import ValidationError


class TestActivityLogService(TestCase):

    def setUp(self):
        # Create a user, post and comment
        self.user = User.objects.create_user(
            email="test@example.com", password="password", full_name="John Doe"
        )
        self.post = Post.objects.create(user=self.user, content="Original post")
        self.comment = Comment.objects.create(
            user=self.user, post=self.post, content="Nice post!"
        )

        # Update post, comment, and user to create additional historical records
        self.post.content = "Updated and changed the post!"
        self.post.save()

        self.comment.content = "Updated and changed the comment!"
        self.comment.save()

        self.user.email = "updatedemail@example.com"
        self.user.save()

    def test_activity_log_success(self):
        # Arrange
        activities = ActivityServices.get_user_activities(self.user.id)

        # Act

        # Find the first activity corresponding to a created Post (history_type '+')
        # returns None if not found
        post_created = next(
            (
                a
                for a in activities
                if isinstance(a.activity.instance, Post)
                and a.activity.history_type == "+"
            ),
            None,
        )

        post_updated = next(
            (
                a
                for a in activities
                if isinstance(a.activity.instance, Post)
                and a.activity.history_type == "~"
            ),
            None,
        )

        comment_created = next(
            (
                a
                for a in activities
                if isinstance(a.activity.instance, Comment)
                and a.activity.history_type == "+"
            ),
            None,
        )

        comment_updated = next(
            (
                a
                for a in activities
                if isinstance(a.activity.instance, Comment)
                and a.activity.history_type == "~"
            ),
            None,
        )

        user_created = next(
            (
                a
                for a in activities
                if isinstance(a.activity.instance, User)
                and a.activity.history_type == "+"
            ),
            None,
        )

        user_updated = next(
            (
                a
                for a in activities
                if isinstance(a.activity.instance, User)
                and a.activity.history_type == "~"
            ),
            None,
        )

        # Assert
        self.assertIsNotNone(post_created)
        self.assertIn("created a post", post_created.description.lower())

        self.assertIsNotNone(post_updated)
        self.assertIn("updated content", post_updated.description.lower())

        self.assertIsNotNone(comment_created)
        self.assertIn("created a comment", comment_created.description.lower())

        self.assertIsNotNone(comment_updated)
        self.assertIn("updated content", comment_updated.description.lower())

        self.assertIsNotNone(user_created)
        self.assertIn("created user", user_created.description.lower())

        self.assertIsNotNone(user_updated)
        self.assertIn("updated email", user_updated.description.lower())
        self.assertIn("to 'updatedemail@example.com'", user_updated.description.lower())

    def test_activity_log_invalid_user_id(self):

        with self.assertRaises(ValidationError):
            ActivityServices.get_user_activities(999)

        with self.assertRaises(ValueError):
            ActivityServices.get_user_activities("Zzzz")
