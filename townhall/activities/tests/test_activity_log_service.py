from django.test import TestCase
from posts.models import Post, Comment
from users.models import User
from activities.services import ActivityServices
from django.forms import ValidationError


class TestActivityLogService(TestCase):

    def setUp(self):
        # Create a user, post and comment
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password",
            full_name="John Doe",
        )
        self.post = Post.objects.create(user=self.user, content="Original post")
        self.comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            content="Nice post!",
        )

        # Update post, comment, user to create additional historical records
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

        # Find first activity for created Post (history_type '+')
        # returns None if not found
        post_created = next(
            (
                a
                for a in activities
                if a.model == "post" and a.activity["history_type"] == "+"
            ),
            None,
        )

        post_updated = next(
            (
                a
                for a in activities
                if a.model == "post" and a.activity["history_type"] == "~"
            ),
            None,
        )

        comment_created = next(
            (
                a
                for a in activities
                if a.model == "comment" and a.activity["history_type"] == "+"
            ),
            None,
        )

        comment_updated = next(
            (
                a
                for a in activities
                if a.model == "comment" and a.activity["history_type"] == "~"
            ),
            None,
        )

        user_created = next(
            (
                a
                for a in activities
                if a.model == "user" and a.activity["history_type"] == "+"
            ),
            None,
        )

        user_updated = next(
            (
                a
                for a in activities
                if a.model == "user" and a.activity["history_type"] == "~"
            ),
            None,
        )

        # Assert
        self.assertIsNotNone(post_created)
        self.assertIn(
            "created a post: 'original post'", post_created.description.lower()
        )

        self.assertIsNotNone(post_updated)
        expected = (
            "updated post: content for post to " "'updated and changed the post!'"
        )
        self.assertIn(expected, post_updated.description.lower())

        self.assertIsNotNone(comment_created)
        self.assertIn(
            "created a comment: 'nice post!'",
            comment_created.description.lower(),
        )

        self.assertIsNotNone(comment_updated)
        expected = "updated comment: content to " "'updated and changed the comment!'"
        self.assertIn(expected, comment_updated.description.lower())

        self.assertIsNotNone(user_created)
        self.assertIn(
            "welcome to atria, you've just created an account!",
            user_created.description.lower(),
        )

        self.assertIsNotNone(user_updated)
        self.assertIn(
            "updated user: email",
            user_updated.description.lower(),
        )

    def test_activity_log_invalid_user_id(self):

        with self.assertRaises(ValidationError):
            ActivityServices.get_user_activities(999)

        with self.assertRaises(ValueError):
            ActivityServices.get_user_activities("Zzzz")
