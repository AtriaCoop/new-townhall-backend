from typing import List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CreateChatData:
    participant_ids: List[int]
    name: str
    created_at: datetime
