import datetime
from typing import Optional, List
from dataclasses import dataclass, field
from django.core.files.uploadedfile import InMemoryUploadedFile


@dataclass
class CreatePostData:
    user_id: int
    content: str
    created_at: datetime
    images: List[InMemoryUploadedFile] = field(default_factory=list)
    pinned: bool = False
    tags: Optional[List[str]] = None
    anonymous: bool = False


@dataclass
class UpdatePostData:
    user_id: int
    content: Optional[str] = None
    # Images omitted — use add_post_images() / delete_post_image() endpoints.
    pinned: Optional[bool] = None
    tags: Optional[List[str]] = None


@dataclass
class CreateCommentData:
    user_id: int
    post_id: int
    content: str
    created_at: datetime
    anonymous: bool = False


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
