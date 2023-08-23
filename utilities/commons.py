from dataclasses import dataclass

from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


@dataclass
class User:
    id: int
    username: str
    role: str
    bio: str
    profile_icon: str
    badges: list[str]
    token: str = None
    github_id: int = None


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
    category: str
    uploaded: int
    updated: int
    type: str = "datapack"


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


#
# DB MODELS
#


class UserModel(Base):
    __tablename__ = "users"

    rowid = Column(Integer, primary_key=True)
    username = Column(Text, unique=True, nullable=False)
    token = Column(Text, unique=True, nullable=False)
    role = Column(Text, nullable=False)
    bio = Column(Text)
    github_id = Column(Integer, unique=True)
    discord_id = Column(Integer, unique=True)
    badges = Column(Text)
    profile_icon = Column(Text, nullable=False)
