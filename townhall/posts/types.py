import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class CreatePostData:
    user_id: int
    content: str
    created_at: datetime
    image: Optional[str] = None


@dataclass
class UpdatePostData:
    content: str
    image: Optional[str] = None


@dataclass
class CreateCommentData:
    user_id: int
    post_id: int
    content: str
    created_at: datetime


@dataclass
class UpdateCommentData:
    content: str


@dataclass
class ReportedPostData:
    user_id: int
    post_id: int
    created_at: datetime
