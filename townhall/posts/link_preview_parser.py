import re
from html.parser import HTMLParser

_URL_RE = re.compile(r"https?://\S+")
_TRAILING_PUNCTUATION = ").,!?;:'\"]}>"


def extract_first_url(text: str) -> str | None:
    """Find the first http(s) URL in a block of post content text, if any, trimming
    trailing punctuation that's clearly not part of the URL itself
    (e.g. a period ending the sentence it was written in)."""
    match = _URL_RE.search(text)
    if not match:
        return None
    return match.group(0).rstrip(_TRAILING_PUNCTUATION) or None


class _MetadataHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = None
        self.og_title = None
        self.og_image = None
        self.og_description = None
        self._in_title_tag = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "title":
            self._in_title_tag = True
        elif tag == "meta":
            key = attrs_dict.get("property") or attrs_dict.get("name")
            content = attrs_dict.get("content")
            if not key or not content:
                return
            if key == "og:title":
                self.og_title = content
            elif key == "og:image":
                self.og_image = content
            elif key == "og:description":
                self.og_description = content

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title_tag = False

    def handle_data(self, data):
        if self._in_title_tag and self.title is None:
            stripped = data.strip()
            if stripped:
                self.title = stripped


def parse_metadata(html: str) -> dict:
    """Extract the title, image, and description of a downloaded webpage of a link."""
    parser = _MetadataHTMLParser()
    parser.feed(html)
    return {
        "title": parser.og_title or parser.title,
        "image": parser.og_image,
        "description": parser.og_description,
    }
