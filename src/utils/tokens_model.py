from pydantic import BaseModel, EmailStr
from typing import Literal


class TokenData(BaseModel):
    username: str
    email: EmailStr
    profile_pic_url: str
    registered_using: Literal['email', 'google', 'facebook']


