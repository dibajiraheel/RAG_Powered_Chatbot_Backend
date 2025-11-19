from pydantic import BaseModel
from typing import Optional, Literal


class CallGraph(BaseModel):
    question: str
    call_which_subgraph: Literal['rag', 'general']