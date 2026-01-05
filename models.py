from pydantic import BaseModel
from typing import Optional, Literal, List, Any

class UrlRequest(BaseModel):
    url: str
    instruction: Optional[str] = None
    schema_map: Optional[dict[str, str]] = None
    page_type: Optional[Literal["list", "detail"]] = None

class ParsedImage(BaseModel):
    url: str
    alt: Optional[str] = None
    description: Optional[str] = None

class ParsedItem(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    snippet: Optional[str] = None
    published_date: Optional[str] = None

class ParsedContent(BaseModel):
    type: Literal["detail", "list", "unknown"]
    title: Optional[str] = None
    summary: Optional[str] = None
    full_text: Optional[str] = None
    published_date: Optional[str] = None
    images: list[ParsedImage] = []
    videos: list[str] = []
    items: list[ParsedItem] = []

class ParseResponse(BaseModel):
    ok: bool
    data: Optional[ParsedContent] = None
    error: Optional[str] = None
