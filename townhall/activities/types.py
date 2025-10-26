from typing import Any
from dataclasses import dataclass


@dataclass
class ActivityWithDescription:
    description: str
    model: str
    activity: dict[str, Any]
