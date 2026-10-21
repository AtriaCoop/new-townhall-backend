from unittest.mock import MagicMock, patch

import requests
from django.test import SimpleTestCase, override_settings

from posts.daos import GifDao
from posts.types import GifProviderError, GifProviderNotConfigured


def giphy_item(**overrides):
    item = {
        "id": "abc123",
        "title": "Happy Cat",
        "images": {
            "original": {
                "mp4": "https://media2.giphy.com/media/abc123/giphy.mp4",
                "width": "480",
                "height": "270",
            },
            "fixed_width": {
                "mp4": "https://media2.giphy.com/media/abc123/200w.mp4",
            },
            "original_still": {
                "url": "https://media2.giphy.com/media/abc123/giphy_s.gif",
            },
        },
    }
    item.update(overrides)
    return item


def giphy_response(items, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.ok = 200 <= status_code < 300
    response.json.return_value = {"data": items}
    return response


@override_settings(GIPHY_API_KEY="k")
class GifDaoTests(SimpleTestCase):

    def test_normalize_maps_giphy_fields(self):
        self.assertEqual(
            GifDao.normalize_giphy_item(giphy_item()),
            {
                "provider": "giphy",
                "id": "abc123",
                "title": "Happy Cat",
                "video_url": "https://media2.giphy.com/media/abc123/giphy.mp4",
                "preview_url": "https://media2.giphy.com/media/abc123/200w.mp4",
                "still_url": "https://media2.giphy.com/media/abc123/giphy_s.gif",
                "width": 480,
                "height": 270,
            },
        )

    def test_normalize_skips_item_missing_mp4(self):
        item = giphy_item()
        del item["images"]["original"]["mp4"]
        self.assertIsNone(GifDao.normalize_giphy_item(item))

    @patch("posts.daos.requests.get")
    def test_search_sends_rating_and_query(self, mock_get):
        mock_get.return_value = giphy_response([giphy_item()])

        GifDao.search("cats & dogs", 30)

        mock_get.assert_called_once_with(
            "https://api.giphy.com/v1/gifs/search",
            params={"api_key": "k", "q": "cats & dogs", "limit": 30, "rating": "pg"},
            timeout=5,
        )

    @patch("posts.daos.requests.get")
    def test_search_drops_items_that_fail_to_normalize(self, mock_get):
        broken = giphy_item(id="broken")
        del broken["images"]["fixed_width"]["mp4"]
        mock_get.return_value = giphy_response([giphy_item(), broken])

        gifs = GifDao.search("cat", 30)

        self.assertEqual(len(gifs), 1)
        self.assertEqual(gifs[0]["id"], "abc123")

    @patch("posts.daos.requests.get")
    def test_trending_calls_trending_url(self, mock_get):
        mock_get.return_value = giphy_response([giphy_item()])

        GifDao.trending(30)

        mock_get.assert_called_once_with(
            "https://api.giphy.com/v1/gifs/trending",
            params={"api_key": "k", "limit": 30, "rating": "pg"},
            timeout=5,
        )

    @patch("posts.daos.requests.get")
    def test_dao_raises_provider_error_on_timeout(self, mock_get):
        mock_get.side_effect = requests.Timeout()
        with self.assertRaises(GifProviderError):
            GifDao.search("cat", 30)

    @patch("posts.daos.requests.get")
    def test_dao_raises_provider_error_on_non_2xx(self, mock_get):
        mock_get.return_value = giphy_response([], status_code=500)
        with self.assertRaises(GifProviderError):
            GifDao.search("cat", 30)

    @patch("posts.daos.requests.get")
    def test_dao_raises_provider_error_on_body_without_data_list(self, mock_get):
        response = giphy_response([])
        response.json.return_value = {"meta": {"msg": "oops"}}
        mock_get.return_value = response
        with self.assertRaises(GifProviderError):
            GifDao.trending(30)

    @override_settings(GIPHY_API_KEY=None)
    @patch("posts.daos.requests.get")
    def test_dao_raises_not_configured_without_key(self, mock_get):
        with self.assertRaises(GifProviderNotConfigured):
            GifDao.search("cat", 30)
        mock_get.assert_not_called()
