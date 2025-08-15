# posts/profanity.py

import re
from typing import Iterable

DEFAULT_PROFANITY_LIST = [
    "fuck",
    "shit",
    "bitch",
    "bastard",
    "asshole",
    "dick",
    "piss",
    "crap",
    "damn",
    "slut",
    "whore",
    "cunt",
    "prick",
    "motherfucker",
    "nigga",
    "nigger",
    "faggot",
    "fag",
    "hell",
    "fucker",
]


def make_censor(words: Iterable[str]) -> re.Pattern:
    escaped = [re.escape(word) for word in words if word.strip()]
    if not escaped:
        return re.compile(r"(?!x)x")
    return re.compile(rf"(?iu)\b(?:{'|'.join(escaped)})\b")


_CENSOR_RE = make_censor(DEFAULT_PROFANITY_LIST)


def censor_text(text: str) -> str:
    if not text:
        return text
    return _CENSOR_RE.sub(lambda m: "*" * len(m.group(0)), text)
