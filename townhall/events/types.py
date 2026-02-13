import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class CreateEventData:
    admin_id: int
    title: str
    description: str
    date: datetime.date
    time: str
    location: str


@dataclass
class UpdateEventData:
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime.date] = None
    time: Optional[str] = None
    location: Optional[str] = None
