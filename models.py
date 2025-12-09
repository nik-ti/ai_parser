from pydantic import BaseModel
from typing import Optional, Any

class UrlRequest(BaseModel):
    url: str
    instruction: Optional[str] = None
    schema_map: Optional[dict[str, str]] = None

class ParseResponse(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[str] = None
