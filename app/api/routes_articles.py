from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, HTTPException, Query, Request

from app import db
from app.schemas import ArticleListResponse, ArticleOut, DeleteArticleResponse, SaveResponse
from app.utils import to_iso_utc, utc_now

router = APIRouter(tags=["articles"])


@router.get("/articles", response_model=ArticleListResponse)
def list_articles(
    request: Request,
    window_hours: int = Query(default=24, ge=1, le=168),
    saved: str = Query(default="all", pattern="^(all|true|false)$"),
    source_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    settings = request.app.state.settings
    effective_window = window_hours if window_hours > 0 else settings.ingestion_window_hours
    cutoff_iso = to_iso_utc(utc_now() - timedelta(hours=effective_window))

    with db.connection(settings.db_path) as conn:
        total, rows = db.list_articles(
            conn,
            cutoff_iso_utc=cutoff_iso,
            saved=saved,
            source_id=source_id,
            limit=limit,
            offset=offset,
        )

    items = [
        ArticleOut(
            id=row["id"],
            source_id=row["source_id"],
            source_name=row["source_name"],
            title=row["title"],
            url=row["url"],
            canonical_url=row["canonical_url"],
            published_at_utc=row["published_at_utc"],
            snippet=row["snippet"] or "",
            image_url=row["image_url"],
            is_saved=bool(row["is_saved"]),
            first_seen_at_utc=row["first_seen_at_utc"],
            last_seen_at_utc=row["last_seen_at_utc"],
        )
        for row in rows
    ]
    return ArticleListResponse(total=total, items=items)


@router.post("/articles/{article_id}/save", response_model=SaveResponse)
def save_article(article_id: str, request: Request):
    settings = request.app.state.settings
    with db.connection(settings.db_path) as conn:
        updated = db.set_article_saved(conn, article_id=article_id, is_saved=True)
    if not updated:
        raise HTTPException(status_code=404, detail="article not found")
    return SaveResponse(article_id=article_id, is_saved=True)


@router.delete("/articles/{article_id}/save", response_model=SaveResponse)
def unsave_article(article_id: str, request: Request):
    settings = request.app.state.settings
    with db.connection(settings.db_path) as conn:
        updated = db.set_article_saved(conn, article_id=article_id, is_saved=False)
    if not updated:
        raise HTTPException(status_code=404, detail="article not found")
    return SaveResponse(article_id=article_id, is_saved=False)


@router.delete("/articles/{article_id}", response_model=DeleteArticleResponse)
def delete_article(article_id: str, request: Request):
    settings = request.app.state.settings
    with db.connection(settings.db_path) as conn:
        deleted = db.delete_article(conn, article_id=article_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="article not found")
    return DeleteArticleResponse(article_id=article_id, deleted=True)
