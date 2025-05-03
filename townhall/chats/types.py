from typing import List
from dataclasses import dataclass


@dataclass
class CreateChatData:
    participant_ids: List[int]
    name: str
