from dataclasses import dataclass

@dataclass
class User:
    id: int
    username: str
    role: str
    bio: str
    profile_icon: str
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