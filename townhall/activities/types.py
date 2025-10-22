from typing import Any
from dataclasses import dataclass


@dataclass
class ActivityWithDescription:
    activity: Any
    description: str
