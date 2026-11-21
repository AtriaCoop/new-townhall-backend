from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from users.models import User


# Tests for GET /post/link-preview/?url=<url>
#
# The endpoint fetches Open Graph metadata for a user-supplied URL and returns
# it as a preview card. Because the server makes the outbound request on behalf
# of the user, the service layer (PostServices.get_link_preview) is mocked in
# every test that reaches it — this avoids real network calls and keeps tests
# focused on endpoint behaviour only.
#
# Tests that are rejected before reaching the service layer (auth check,
# parameter validation) do not need @patch because the service is never called.
class LinkPreviewEndpointTests(TestCase):
    def setUp(self):
        # Clear cache before each test so that rate-limit counters from a
        # previous test do not bleed into the next one.
        cache.clear()
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)
        self.client = APIClient()
        self.test_user = User.objects.get(pk=1)
        # Fixture passwords may be stored in plain text; hash it so that
        # client.login() can authenticate against it correctly.
        self.test_user.password = make_password("987password")
        self.test_user.save()
        self.url = "/post/link-preview/"

    def _login(self):
        self.client.login(username=self.test_user.email, password="987password")

    @patch("posts.views.PostServices.get_link_preview")
    def test_returns_preview_data_for_authenticated_user(self, mock_get_preview):
        # @patch replaces get_link_preview with a fake that returns fixed data,
        # so no real HTTP fetch happens. This isolates the test to endpoint
        # behaviour: does it call the service with the right URL and return the
        # result to the client?
        # Arrange
        self._login()
        mock_get_preview.return_value = {
            "title": "Example Domain",
            "image": None,
            "description": None,
            "domain": "example.com",
        }

        # Act
        response = self.client.get(self.url, {"url": "https://example.com"})

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["domain"], "example.com")
        # Verify the endpoint passes the URL to the service unchanged.
        mock_get_preview.assert_called_once_with("https://example.com")

    def test_rejects_unauthenticated_request(self):
        # No @patch needed: the auth check fires before the service is called,
        # so get_link_preview is never reached.
        # Without authentication anyone could use the server as a proxy to fetch
        # arbitrary URLs, including internal network resources (SSRF risk).
        # Act
        response = self.client.get(self.url, {"url": "https://example.com"})

        # Assert
        self.assertEqual(response.status_code, 401)

    def test_missing_url_param_returns_400(self):
        # No @patch needed: parameter validation fires before the service is
        # called. Without a URL there is nothing to fetch.
        # Arrange
        self._login()

        # Act
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, 400)

    @patch("posts.views.PostServices.get_link_preview")
    def test_unfetchable_url_returns_422(self, mock_get_preview):
        # get_link_preview returns None when it cannot fetch a URL — either
        # because is_safe_url rejected it (SSRF guard) or the host was
        # unreachable. The endpoint must translate None into 422 rather than
        # silently returning an empty 200, so the client knows the preview
        # failed rather than just being empty.
        # Arrange
        self._login()
        mock_get_preview.return_value = None

        # Act
        response = self.client.get(self.url, {"url": "https://unreachable.example"})

        # Assert
        self.assertEqual(response.status_code, 422)

    @patch("posts.views.PostServices.get_link_preview")
    def test_rate_limit_returns_429_after_threshold(self, mock_get_preview):
        # LinkPreviewThrottle (defined in views.py) allows 20 requests per
        # minute per user. Without this limit an attacker could loop requests
        # to make the server fetch arbitrary URLs at high volume (DoS risk).
        #
        # get_link_preview is mocked so 21 real fetches are not made — the
        # rate-limit counter tracks request count, not fetch outcomes, so
        # mocking does not affect throttle behaviour.
        #
        # 21 requests is the minimum to confirm the exact boundary:
        #   - requests 1-20 (statuses[0:20]) must all be 200
        #   - request 21   (statuses[-1])    must be 429
        # Checking both directions ensures the throttle is neither too strict
        # (firing before 20) nor too lenient (never firing).
        # Arrange
        self._login()
        mock_get_preview.return_value = {
            "title": "Example Domain",
            "image": None,
            "description": None,
            "domain": "example.com",
        }

        # Act — LinkPreviewThrottle allows 20/min; the 21st request should be throttled.
        statuses = [
            self.client.get(self.url, {"url": "https://example.com"}).status_code
            for _ in range(21)
        ]

        # Assert
        self.assertEqual(statuses[-1], 429)
        self.assertTrue(all(code == 200 for code in statuses[:20]))
