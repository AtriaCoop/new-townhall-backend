from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from chats.models import Chat, GroupMessage, Message
from posts.models import Comment, Post
from users.models import User


class ExportUserDataEndpointTests(TestCase):
    """
    Integration tests for the GET /user/export/ endpoint.

    Covers authentication enforcement, format validation, and data
    isolation, ensuring users can only export their own data.
    """

    def setUp(self):
        """
        Set up two users (owner and other) each with a post, comment,
        direct message, and group message. Tests use self.user as the
        authenticated user and verify self.other_user's data is excluded.
        """

        self.client = APIClient()
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="test-password",
            full_name="Owner User",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="test-password",
            full_name="Other User",
        )

        self.post = Post.objects.create(
            user=self.user,
            content="Owner post",
            created_at=timezone.now(),
        )
        self.other_post = Post.objects.create(
            user=self.other_user,
            content="Other post",
            created_at=timezone.now(),
        )
        Comment.objects.create(
            user=self.user,
            post=self.post,
            content="Owner comment",
            created_at=timezone.now(),
        )
        Comment.objects.create(
            user=self.other_user,
            post=self.other_post,
            content="Other comment",
            created_at=timezone.now(),
        )

        chat = Chat.objects.create(name="Direct chat")
        chat.participants.set([self.user, self.other_user])
        Message.objects.create(
            user=self.user,
            chat=chat,
            content="Owner direct message",
            sent_at=timezone.now(),
        )
        Message.objects.create(
            user=self.other_user,
            chat=chat,
            content="Other direct message",
            sent_at=timezone.now(),
        )
        GroupMessage.objects.create(
            user=self.user,
            group_name="general",
            content="Owner group message",
            sent_at=timezone.now(),
        )
        GroupMessage.objects.create(
            user=self.other_user,
            group_name="general",
            content="Other group message",
            sent_at=timezone.now(),
        )

    def test_export_requires_authentication(self):
        """Unauthenticated requests should receive a 401 response."""

        response = self.client.get("/user/export/")

        self.assertEqual(response.status_code, 401)

    def test_export_rejects_unknown_format(self):
        """Requests with an unsupported format parameter should receive a 400 response (e.g. format=pdf)."""

        self.client.force_login(self.user)

        response = self.client.get("/user/export/?format=pdf")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"], "format must be either 'json' or 'csv'"
        )

    def test_export_json_returns_only_current_users_data(self):
        """
        JSON export should return 200 with the correct Content-Disposition
        header and only include the authenticated user's posts, comments,
        direct messages, and group messages.
        """

        self.client.force_login(self.user)

        response = self.client.get("/user/export/?format=json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="townhall-user-data.json"',
        )

        payload = response.json()
        self.assertEqual(payload["user"]["id"], self.user.id)
        self.assertEqual([post["content"] for post in payload["posts"]], ["Owner post"])
        self.assertEqual(
            [comment["content"] for comment in payload["comments"]],
            ["Owner comment"],
        )
        self.assertEqual(
            [message["content"] for message in payload["direct_messages"]],
            ["Owner direct message"],
        )
        self.assertEqual(
            [message["content"] for message in payload["group_messages"]],
            ["Owner group message"],
        )

    def test_export_csv_streams_only_current_users_data(self):
        """
        CSV export should return 200 with the correct Content-Disposition
        header and stream only the authenticated user's data, excluding
        any content belonging to other users.
        """
        
        self.client.force_login(self.user)

        response = self.client.get("/user/export/?format=csv")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="townhall-user-data.csv"',
        )

        content = b"".join(response.streaming_content).decode()
        self.assertIn("Owner post", content)
        self.assertIn("Owner comment", content)
        self.assertIn("Owner direct message", content)
        self.assertIn("Owner group message", content)
        self.assertNotIn("Other post", content)
        self.assertNotIn("Other comment", content)
        self.assertNotIn("Other direct message", content)
        self.assertNotIn("Other group message", content)
