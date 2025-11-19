from pydantic import BaseModel, EmailStr
from typing import Optional


class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    profile_pic_url: Optional[str] = ''
    

