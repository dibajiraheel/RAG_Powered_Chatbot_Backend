from pydantic import BaseModel
from typing import Optional


class EmailResponse(BaseModel):
    email_sent: bool
    detail: Optional[str] = None






