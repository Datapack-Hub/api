from pydantic import BaseModel


from typing import List


class BadgesJsonBody(BaseModel):
    badges: List[str]

class UserEditBody(BaseModel):
    username: str
    bio: str
    role: str = None
    
class PostNewProjectBody(BaseModel):
    type: str
    url: str
    title: str
    description: str
    body: str
    category: List[str]
    icon: str = None

class EditProjectBody(BaseModel):
    title: str
    description: str
    body: str
    category: List[str]
    icon: str = None