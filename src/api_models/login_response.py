from pydantic import BaseModel
from typing import Optional



class APILoginResponse(BaseModel):
    task_completed: bool
    detail: list[str]
    status_code: Optional[int] = 0