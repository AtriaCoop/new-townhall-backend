from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CreateChatData:
    participant_ids: List[int]
    name: str


@dataclass
class CreateMessageData:
    user_id: int
    chat_id: int
    content: str
    image_content: Optional[str] = None
    sent_at: Optional[datetime] = None
