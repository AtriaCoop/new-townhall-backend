from typing import Optional, List
from dataclasses import dataclass
import datetime


@dataclass
class CreateUserData:
    email: str
    password: str


@dataclass
class UpdateUserData:
    id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    pronouns: Optional[str] = None
    title: Optional[str] = None
    primary_organization: Optional[str] = None
    other_organizations: Optional[str] = None
    other_networks: Optional[str] = None
    about_me: Optional[str] = None
    skills_interests: Optional[str] = None
    profile_image: Optional[str] = None
    profile_header: Optional[str] = None
    receive_emails: Optional[bool] = None
    show_email: Optional[bool] = None
    show_in_directory: Optional[bool] = None
    allow_dms: Optional[bool] = None
    tags: Optional[List[str]] = None
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    x_url: Optional[str] = None
    instagram_url: Optional[str] = None


@dataclass
class FilterUserData:
    full_name: Optional[str] = None
    email: Optional[str] = None


@dataclass
class CreateReportData:
    user_id: int
    content: str
    created_at: datetime
