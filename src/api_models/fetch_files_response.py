from pydantic import BaseModel
from typing import Optional




class APIFetchFilesResponse(BaseModel):
    task_completed: bool
    detail: list
    status_code: Optional[int] = 0



