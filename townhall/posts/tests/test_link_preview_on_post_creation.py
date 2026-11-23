from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from posts.services import PostServices
from posts.types import CreatePostData
from users.models import User


# Tests for the link-preview behaviour inside PostServices.create_post.
#
# There are two separate link-preview flows in this feature:
#   1. Composer (real-time): while the user is typing, the frontend calls
#      GET /post/link-preview/ to show a preview card — result is NOT saved.
#   2. On save (this file): when the user submits the post, create_post fetches
#      the preview again and persists it to the DB alongside the post content.
#
# Fetching twice might seem redundant, but:
#   - The second fetch is served from cache (no extra network call).
#   - Re-fetching on the server ensures we only store data the server itself
#     verified — trusting the frontend to pass the composer result would allow
#     a malicious user to submit tampered preview data.
#
# Both PostDao.create_post and get_link_preview are mocked in every test to
# avoid real DB writes and real network fetches.
class TestLinkPreviewOnPostCreation(TestCase):
    def setUp(self):
        # Create a minimal user directly (no fixture needed — only user_id is
        # required by CreatePostData).
        self.user = User.objects.create(email="user@example.com", is_staff=False)

    @patch("posts.services.PostDao.create_post")
    @patch("posts.services.PostServices.get_link_preview")
    def test_post_with_url_gets_link_preview_populated(
        self, mock_get_preview, mock_create
    ):
        # When the post body contains a URL, create_post must:
        #   1. Call get_link_preview with that URL.
        #   2. Pass the result to PostDao.create_post as link_preview.
        # assert_called_once_with on mock_create verifies both that the DAO was
        # called and that it received the correct preview payload.
        # Arrange
        mock_get_preview.return_value = {
            "title": "Example",
            "image": None,
            "description": None,
            "domain": "example.com",
        }
        mock_create.return_value = SimpleNamespace(content="Check https://example.com")
        post_data = CreatePostData(
            content="Check this out: https://example.com",
            user_id=self.user.id,
            created_at=timezone.now(),
        )

        # Act
        PostServices.create_post(post_data)

        # Assert
        mock_get_preview.assert_called_once_with("https://example.com")
        mock_create.assert_called_once_with(
            post_data=post_data,
            link_preview={
                "title": "Example",
                "image": None,
                "description": None,
                "domain": "example.com",
            },
        )

    @patch("posts.services.PostDao.create_post")
    @patch("posts.services.PostServices.get_link_preview")
    def test_post_without_url_skips_link_preview_fetch(
        self, mock_get_preview, mock_create
    ):
        # When there is no URL in the post body, get_link_preview must not be
        # called at all — fetching would be pointless and wasteful.
        # link_preview=None is passed to the DAO so the column is explicitly
        # empty rather than left undefined.
        # Arrange
        mock_create.return_value = SimpleNamespace(content="Just plain text")
        post_data = CreatePostData(
            content="Just plain text, no links here",
            user_id=self.user.id,
            created_at=timezone.now(),
        )

        # Act
        PostServices.create_post(post_data)

        # Assert
        mock_get_preview.assert_not_called()
        mock_create.assert_called_once_with(post_data=post_data, link_preview=None)

    @patch("posts.services.PostDao.create_post")
    @patch("posts.services.PostServices.get_link_preview")
    def test_failed_preview_fetch_still_creates_post(
        self, mock_get_preview, mock_create
    ):
        # get_link_preview returns None when a URL is unsafe (SSRF guard) or
        # unreachable. The post must still be created successfully — a failed
        # preview fetch is not a reason to block the user's post. The preview
        # is an optional enrichment, not a requirement.
        # Arrange — get_link_preview fails closed (unsafe/unreachable URL, etc.)
        mock_get_preview.return_value = None
        mock_create.return_value = SimpleNamespace(content="Check https://example.com")
        post_data = CreatePostData(
            content="Check https://example.com",
            user_id=self.user.id,
            created_at=timezone.now(),
        )

        # Act
        post = PostServices.create_post(post_data)

        # Assert — post creation succeeds regardless of preview outcome.
        self.assertIsNotNone(post)
        mock_create.assert_called_once_with(post_data=post_data, link_preview=None)
