from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase

from posts.services import PostServices


# Helper that builds a fake requests.get() response with the same structure
# (status_code, headers, raw.read()) as a real HTTP response. Defined once
# here to avoid repeating the same MagicMock setup in every test.
def _mock_html_response(html: str, status_code: int = 200, headers=None):
    response = MagicMock()
    response.status_code = status_code
    response.headers = {"Content-Type": "text/html; charset=utf-8", **(headers or {})}
    response.encoding = "utf-8"
    response.raw.read.return_value = html.encode("utf-8")
    return response


# Tests for PostServices.get_link_preview — the core method that:
#   1. Checks the URL is safe (SSRF guard via is_safe_url)
#   2. Fetches the page HTML via requests.get
#   3. Parses OGP metadata from the HTML
#   4. Caches the result to avoid redundant fetches
#
# Both is_safe_url and requests.get are mocked in every test so no real network
# calls are made. cache.clear() in setUp ensures cached results from one test
# do not affect the next.
class TestGetLinkPreview(TestCase):
    def setUp(self):
        cache.clear()

    @patch("posts.services.is_safe_url", return_value=True)
    @patch("posts.services.requests.get")
    def test_returns_parsed_metadata_for_safe_url(self, mock_get, mock_is_safe):
        # Basic happy path: safe URL → fetch → parse OGP → return metadata.
        # The "domain" field is not in OGP tags; the service extracts it from
        # the URL itself and appends it to the result.
        # Arrange
        mock_get.return_value = _mock_html_response(
            '<html><head><meta property="og:title" content="Hello"></head></html>'
        )

        # Act
        result = PostServices.get_link_preview("https://example.com")

        # Assert
        self.assertEqual(result["title"], "Hello")
        self.assertEqual(result["domain"], "example.com")

    @patch("posts.services.is_safe_url", return_value=False)
    @patch("posts.services.requests.get")
    def test_unsafe_url_is_rejected_without_fetching(self, mock_get, mock_is_safe):
        # When is_safe_url rejects the URL (private IP, loopback, etc.),
        # requests.get must never be called — the SSRF guard only works if
        # the fetch is blocked entirely, not just the result discarded.
        # Act
        result = PostServices.get_link_preview("https://internal.example")

        # Assert
        self.assertIsNone(result)
        mock_get.assert_not_called()

    @patch("posts.services.is_safe_url", return_value=True)
    @patch("posts.services.requests.get")
    def test_non_html_content_type_is_rejected(self, mock_get, mock_is_safe):
        # Only text/html responses contain OGP tags worth parsing. Non-HTML
        # content (PDFs, images, etc.) must be rejected to avoid attempting
        # to parse binary data and potentially loading large files into memory.
        # Arrange
        mock_get.return_value = _mock_html_response(
            "not html", headers={"Content-Type": "application/pdf"}
        )

        # Act
        result = PostServices.get_link_preview("https://example.com/file.pdf")

        # Assert
        self.assertIsNone(result)

    @patch("posts.services.is_safe_url")
    @patch("posts.services.requests.get")
    def test_follows_redirect_and_revalidates_target(self, mock_get, mock_is_safe):
        # When a URL redirects (302), the redirect target must also pass
        # is_safe_url. Checking only the original URL would allow an attacker
        # to use a safe-looking URL that redirects to an internal address.
        # mock_get.side_effect provides two responses in sequence:
        # first the 302, then the final page.
        # Arrange — both the original and redirect target must pass is_safe_url.
        mock_is_safe.return_value = True
        redirect_response = MagicMock()
        redirect_response.status_code = 302
        redirect_response.headers = {"Location": "https://final.example.com/"}
        final_response = _mock_html_response("<title>Final Page</title>")
        mock_get.side_effect = [redirect_response, final_response]

        # Act
        result = PostServices.get_link_preview("https://short.example/abc")

        # Assert
        self.assertEqual(result["domain"], "final.example.com")
        # is_safe_url must have been called twice: once for the original URL,
        # once for the redirect target.
        self.assertEqual(mock_is_safe.call_count, 2)

    @patch("posts.services.is_safe_url")
    @patch("posts.services.requests.get")
    def test_redirect_to_unsafe_target_is_rejected(self, mock_get, mock_is_safe):
        # Concrete SSRF scenario via URL shortener: the original URL passes the
        # safety check, but the redirect destination is the AWS metadata endpoint
        # (169.254.169.254). The second is_safe_url call must catch this and
        # abort — returning None rather than leaking cloud credentials.
        # mock_is_safe.side_effect returns True for the first call, False for
        # the second.
        # Arrange — original URL is safe, but the redirect target is not.
        mock_is_safe.side_effect = [True, False]
        redirect_response = MagicMock()
        redirect_response.status_code = 302
        redirect_response.headers = {"Location": "http://169.254.169.254/latest/"}
        mock_get.return_value = redirect_response

        # Act
        result = PostServices.get_link_preview("https://short.example/abc")

        # Assert
        self.assertIsNone(result)

    @patch("posts.services.is_safe_url", return_value=True)
    @patch("posts.services.requests.get")
    def test_successful_result_is_cached(self, mock_get, mock_is_safe):
        # A successful preview result is stored in cache so that a second call
        # for the same URL is served without a network round-trip.
        # This is what makes the double-fetch pattern safe to use: the composer
        # fetches once while the user is typing; create_post fetches again on
        # save — but the second fetch hits the cache, not the network.
        # Arrange
        mock_get.return_value = _mock_html_response("<title>Cached Page</title>")

        # Act
        PostServices.get_link_preview("https://example.com")
        PostServices.get_link_preview("https://example.com")

        # Assert — second call should be served from cache, not re-fetched.
        self.assertEqual(mock_get.call_count, 1)
