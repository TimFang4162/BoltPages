"""Data models for blog posts and metadata."""

from dataclasses import dataclass, field
from datetime import date
from datetime import datetime as dt_datetime
from pathlib import Path
from typing import Any


@dataclass
class PostMetadata:
    title: str
    post_date: date | str
    tags: list[str] = field(default_factory=list)
    draft: bool = False
    
    def __post_init__(self) -> None:
        if isinstance(self.post_date, str):
            self.post_date = dt_datetime.strptime(self.post_date, "%Y-%m-%d").date()  # type: ignore[assignment]


@dataclass
class Post:
    path: Path
    source: str
    hash: str
    metadata: dict[str, Any] = field(default_factory=dict)
    content: str = ""
    
    @property
    def is_draft(self) -> bool:
        return self.metadata.get("draft", False)
    
    @property
    def is_page(self) -> bool:
        return self.metadata.get("type", "post") == "page"
    
    @property
    def title(self) -> str:
        return self.metadata.get("title", "")
    
    @property
    def post_date(self) -> str:
        return self.metadata.get("date", "")
    
    @property
    def tags(self) -> list[str]:
        tags = self.metadata.get("tags", [])
        return tags if tags else []
    
    @property
    def slug(self) -> str | None:
        return self.metadata.get("slug")


@dataclass
class TagCount:
    name: str
    count: int
