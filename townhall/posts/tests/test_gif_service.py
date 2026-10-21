from unittest.mock import patch

from django.test import SimpleTestCase

from posts.services import GifServices

FAKE_GIFS = [{"provider": "giphy", "id": "abc123"}]


@patch("posts.services.GifDao")
class GifServicesTests(SimpleTestCase):

    def test_search_passes_query_and_page_size(self, mock_dao):
        mock_dao.search.return_value = FAKE_GIFS

        result = GifServices.search_gifs("cat")

        mock_dao.search.assert_called_once_with("cat", GifServices.PAGE_SIZE)
        self.assertEqual(result, FAKE_GIFS)

    def test_trending_uses_page_size(self, mock_dao):
        mock_dao.trending.return_value = FAKE_GIFS

        result = GifServices.trending_gifs()

        mock_dao.trending.assert_called_once_with(GifServices.PAGE_SIZE)
        self.assertEqual(result, FAKE_GIFS)

    def test_page_size_is_30(self, mock_dao):
        self.assertEqual(GifServices.PAGE_SIZE, 30)
