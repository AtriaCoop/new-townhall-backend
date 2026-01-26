import datetime
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class CreatePostData:
    user_id: int
    content: str
    created_at: datetime
    image: Optional[str] = None
    pinned: bool = False
    tags: Optional[List[str]] = None


@dataclass
class UpdatePostData:
    user_id: int
    content: Optional[str] = None
    image: Optional[str] = None
    pinned: Optional[bool] = None
    tags: Optional[List[str]] = None


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


@dataclass
class ToggleReactionData:
    user_id: int
    post_id: int
    reaction_type: str
