from pydantic import BaseModel
from typing import List, Optional, Any

class SolveRequest(BaseModel):
    query: str
    task: str = "auto"        # auto, solve, simplify, differentiate, integrate, factor, expand
    vars: Optional[List[str]] = None

class SolveResponse(BaseModel):
    ok: bool
    task: str
    detected: dict
    result: Any
    steps: Optional[List[str]] = None
    warnings: Optional[List[str]] = None