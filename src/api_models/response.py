from pydantic import BaseModel
from typing import Optional, Union, List



class APIResponse(BaseModel):
    task_completed: bool
    detail: Optional[Union[str, list]] = ''
    status_code: Optional[int] = 400