from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ArticleOut(BaseModel):
    id: str
    source_id: str
    source_name: str
    title: str
    url: str
    canonical_url: str
    published_at_utc: str
    snippet: str
    image_url: Optional[str] = None
    is_saved: bool
    first_seen_at_utc: str
    last_seen_at_utc: str


class ArticleListResponse(BaseModel):
    total: int
    items: list[ArticleOut]


class SaveResponse(BaseModel):
    article_id: str
    is_saved: bool


class DeleteArticleResponse(BaseModel):
    article_id: str
    deleted: bool


class IngestionRunOut(BaseModel):
    id: str
    started_at_utc: str
    completed_at_utc: Optional[str] = None
    status: str
    new_count: int
    updated_count: int
    skipped_count: int
    error_count: int
    notes: dict[str, Any] = Field(default_factory=dict)


class TriggerResponse(BaseModel):
    accepted: bool
    message: str
    run: Optional[IngestionRunOut] = None


class IngestionStatusResponse(BaseModel):
    running: bool
    last_run: Optional[IngestionRunOut] = None


class SourceHealthOut(BaseModel):
    source_id: str
    source_name: str
    status: str
    checked_at_utc: str
    detail: str


class SourceHealthResponse(BaseModel):
    timestamp_utc: str
    sources: list[SourceHealthOut]
