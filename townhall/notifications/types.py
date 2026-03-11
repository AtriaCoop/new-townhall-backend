from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateNotificationData:
    recipient_id: int
    notification_type: str
    actor_id: Optional[int] = None
    target_id: Optional[int] = None
    detail: str = ""
