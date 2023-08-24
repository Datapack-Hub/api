from dataclasses import dataclass

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


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

    rowid:Mapped[int] = mapped_column(primary_key=True)
    username:Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    token:Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    role:Mapped[str] = mapped_column(Text, nullable=False)
    bio:Mapped[str] = mapped_column(Text)
    github_id:Mapped[int] = mapped_column(unique=True, nullable=True)
    discord_id:Mapped[int] = mapped_column(unique=True, nullable=True)
    badges:Mapped[str] = mapped_column(Text, nullable=True)
    profile_icon:Mapped[str] = mapped_column(Text, nullable=False)


class ProjectModel(Base):
    __tablename__ = "projects"

    rowid:Mapped[int] = mapped_column(primary_key=True)
    type:Mapped[str] = mapped_column(Text, nullable=False)
    author:Mapped[int] = mapped_column(ForeignKey("users.rowid"), nullable=False)
    title:Mapped[str] = mapped_column(Text, nullable=False)
    description:Mapped[str] = mapped_column(Text, nullable=False)
    body:Mapped[str] = mapped_column(Text, nullable=False)
    icon:Mapped[str] = mapped_column(Text)
    url:Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    status:Mapped[str] = mapped_column(Text, default="draft", nullable=False)
    category:Mapped[str] = mapped_column(Text, nullable=False)
    uploaded:Mapped[int] = mapped_column(Integer, nullable=False)
    updated:Mapped[int] = mapped_column(Integer, nullable=False)
    mod_message:Mapped[str] = mapped_column(Text)
    downloads:Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    featured_until:Mapped[int] = mapped_column(Integer)
    licence:Mapped[str] = mapped_column(Text)
    dependencies:Mapped[str] = mapped_column(Text)
