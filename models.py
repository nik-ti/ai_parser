from pydantic import BaseModel
from typing import Optional, Any

class UrlRequest(BaseModel):
    url: str

class ParseResponse(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[str] = None
