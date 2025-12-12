from pydantic import BaseModel
from typing import Optional, Any, Literal

class UrlRequest(BaseModel):
    url: str
    instruction: Optional[str] = None
    schema_map: Optional[dict[str, str]] = None
    page_type: Optional[Literal["list", "detail"]] = None  # Override auto-detection

class ParseResponse(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[str] = None
