from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from posts.types import GifProviderError, GifProviderNotConfigured
from users.models import User

FAKE_GIF = {
    "provider": "giphy",
    "id": "abc123",
    "title": "Happy Cat",
    "video_url": "https://media2.giphy.com/media/abc123/giphy.mp4",
    "preview_url": "https://media2.giphy.com/media/abc123/200w.mp4",
    "still_url": "https://media2.giphy.com/media/abc123/giphy_s.gif",
    "width": 480,
    "height": 270,
}
UNAVAILABLE = {"error": "GIF search is unavailable right now."}


@patch("posts.views.GifServices")
class GifEndpointTests(TestCase):

    def setUp(self):
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)
        self.client = APIClient()
        user = User.objects.get(pk=1)
        user.password = make_password("987password")
        user.save()
        self.client.login(username=user.email, password="987password")

    def test_trending_returns_gifs(self, mock_services):
        mock_services.trending_gifs.return_value = [FAKE_GIF]

        response = self.client.get("/gifs/trending/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"gifs": [FAKE_GIF]})

    def test_search_returns_gifs(self, mock_services):
        mock_services.search_gifs.return_value = [FAKE_GIF]

        response = self.client.get("/gifs/search/", {"q": "cat"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"gifs": [FAKE_GIF]})
        mock_services.search_gifs.assert_called_once_with("cat")

    def test_search_strips_whitespace(self, mock_services):
        mock_services.search_gifs.return_value = []

        self.client.get("/gifs/search/", {"q": "  cat  "})

        mock_services.search_gifs.assert_called_once_with("cat")

    def test_search_without_q_returns_400(self, mock_services):
        response = self.client.get("/gifs/search/")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Search text is required."})
        mock_services.search_gifs.assert_not_called()

    def test_search_whitespace_only_returns_400(self, mock_services):
        response = self.client.get("/gifs/search/", {"q": "   "})

        self.assertEqual(response.status_code, 400)
        mock_services.search_gifs.assert_not_called()

    def test_search_too_long_returns_400(self, mock_services):
        response = self.client.get("/gifs/search/", {"q": "a" * 51})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Search text is too long."})
        mock_services.search_gifs.assert_not_called()

    def test_search_at_max_length_is_allowed(self, mock_services):
        mock_services.search_gifs.return_value = []

        response = self.client.get("/gifs/search/", {"q": "a" * 50})

        self.assertEqual(response.status_code, 200)

    def test_search_requires_login(self, mock_services):
        self.client.logout()

        response = self.client.get("/gifs/search/", {"q": "cat"})

        self.assertEqual(response.status_code, 401)
        mock_services.search_gifs.assert_not_called()

    def test_trending_requires_login(self, mock_services):
        self.client.logout()

        response = self.client.get("/gifs/trending/")

        self.assertEqual(response.status_code, 401)
        mock_services.trending_gifs.assert_not_called()

    def test_search_returns_502_when_giphy_fails(self, mock_services):
        mock_services.search_gifs.side_effect = GifProviderError()

        response = self.client.get("/gifs/search/", {"q": "cat"})

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json(), UNAVAILABLE)

    def test_search_returns_503_without_api_key(self, mock_services):
        mock_services.search_gifs.side_effect = GifProviderNotConfigured()

        response = self.client.get("/gifs/search/", {"q": "cat"})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), UNAVAILABLE)

    def test_trending_returns_502_when_giphy_fails(self, mock_services):
        mock_services.trending_gifs.side_effect = GifProviderError()

        response = self.client.get("/gifs/trending/")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json(), UNAVAILABLE)
