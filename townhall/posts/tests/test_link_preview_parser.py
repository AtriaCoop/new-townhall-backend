from django.test import TestCase

from posts.link_preview_parser import extract_first_url, parse_metadata


# Tests for two pure parsing functions used in the link-preview pipeline:
#
#   extract_first_url(text) — finds the first URL in a post body string.
#   parse_metadata(html)    — extracts OGP tags from a fetched page's HTML.
#
# OGP (Open Graph Protocol) is a standard that lets pages declare structured
# metadata (title, image, description) inside <meta> tags in <head>. Social
# platforms read these tags to generate preview cards when a URL is shared.
# parse_metadata reads the raw HTML string returned by fetching a URL and
# pulls out those tags.
#
# Neither function makes network calls, so no @patch is needed in any test.


class TestExtractFirstUrl(TestCase):
    def test_finds_url_in_sentence(self):
        # Basic case: URL embedded in surrounding text is correctly identified.
        # Arrange / Act
        result = extract_first_url("Check this out: https://example.com now")

        # Assert
        self.assertEqual(result, "https://example.com")

    def test_strips_trailing_punctuation(self):
        # A URL at the end of a sentence is often followed by punctuation (. , !)
        # that is not part of the URL itself. If not stripped, the fetched URL
        # would be wrong (e.g. "https://example.com/page." returns a 404).
        # Arrange / Act
        result = extract_first_url("See https://example.com/page.")

        # Assert
        self.assertEqual(result, "https://example.com/page")

    def test_returns_none_when_no_url_present(self):
        # None signals to create_post that no preview fetch is needed,
        # avoiding an unnecessary network call.
        # Arrange / Act
        result = extract_first_url("Just a plain sentence with no link.")

        # Assert
        self.assertIsNone(result)

    def test_returns_first_url_when_multiple_present(self):
        # Only one preview card is shown per post, so only the first URL matters.
        # Arrange / Act
        result = extract_first_url(
            "First https://one.example.com then https://two.example.com"
        )

        # Assert
        self.assertEqual(result, "https://one.example.com")


class TestParseMetadata(TestCase):
    def test_extracts_open_graph_tags(self):
        # OGP tags (og:title, og:image, og:description) take priority over the
        # plain <title> tag when both are present — OGP values are specifically
        # intended for link previews, so they are more reliable.
        # The html string here simulates what a real HTTP fetch would return.
        # Arrange
        html = """
        <html><head>
            <title>Fallback Title</title>
            <meta property="og:title" content="OG Title">
            <meta property="og:image" content="https://example.com/img.png">
            <meta property="og:description" content="A description">
        </head></html>
        """

        # Act
        result = parse_metadata(html)

        # Assert
        self.assertEqual(
            result,
            {
                "title": "OG Title",
                "image": "https://example.com/img.png",
                "description": "A description",
            },
        )

    def test_falls_back_to_title_tag_when_no_og_title(self):
        # Many pages (older sites, simple pages) do not include OGP tags.
        # Falling back to <title> ensures those pages still get a usable
        # preview title rather than showing nothing.
        # Arrange
        html = "<html><head><title>Just A Title</title></head></html>"

        # Act
        result = parse_metadata(html)

        # Assert
        self.assertEqual(result["title"], "Just A Title")
        self.assertIsNone(result["image"])
        self.assertIsNone(result["description"])

    def test_empty_html_returns_all_none(self):
        # A fetch can succeed (HTTP 200) but return empty content. The parser
        # must handle this gracefully without raising an exception.
        # Arrange / Act
        result = parse_metadata("")

        # Assert
        self.assertEqual(result, {"title": None, "image": None, "description": None})

    def test_meta_name_attribute_is_also_recognized(self):
        # OGP tags can be written two ways:
        #   <meta property="og:title" content="...">  (standard)
        #   <meta name="og:title"     content="...">  (older convention)
        # Both must be recognised; otherwise pages using the older style
        # would silently produce a preview with no title.
        # Arrange — some pages use name= instead of property=
        html = (
            '<html><head><meta name="og:title" content="Name Attr Title"></head></html>'
        )

        # Act
        result = parse_metadata(html)

        # Assert
        self.assertEqual(result["title"], "Name Attr Title")
