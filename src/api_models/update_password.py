from pydantic import BaseModel




class UpdatePassword(BaseModel):
    email: str
    password: str




