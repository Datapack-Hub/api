from dataclasses import dataclass
from typing import TypedDict


@dataclass
class User:
    id: int
    username: str
    role: str
    bio: str
    profile_icon: str
    badges: list[str] | None = None
    token: str | None = None
    github_id: int | None = None
    join_date: int = 0


@dataclass
class Notification:
    id: int
    message: str
    description: str
    read: bool
    type: int
    user: str


@dataclass
class Project:
    id: int
    author: int
    title: str
    description: str
    body: str
    icon_url: str
    slug: str
    status: str
    category: list[str]
    uploaded: int
    updated: int
    type: str = "datapack"
    mod_message: str | None = None
    downloads: int = 0
    dependencies: str | None = None  # unimplemented
    licence: str | None = None  # unimplemented
    featured_until: int = 0


@dataclass
class Version:
    id: int
    name: str
    code: str
    description: str
    DP_download_url: str
    RP_download_url: str
    minecraft_versions: str
    project_id: int


@dataclass(frozen=True)
class Comment:
    id: int
    author: int
    content: str
    replies: int

class PlayerBanData(TypedDict):
    reason: str
    expires: int