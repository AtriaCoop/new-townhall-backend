from typing import Optional, List
from dataclasses import dataclass


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
    tags: Optional[List[str]] = None


@dataclass
class FilterUserData:
    full_name: Optional[str] = None
    email: Optional[str] = None
