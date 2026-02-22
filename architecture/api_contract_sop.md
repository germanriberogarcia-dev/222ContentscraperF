# API Contract SOP

## Goal
Provide stable JSON interfaces for dashboard integration.

## Endpoints
- `GET /api/articles`
- `POST /api/articles/{article_id}/save`
- `DELETE /api/articles/{article_id}/save`
- `POST /api/ingestion/run`
- `GET /api/ingestion/status`
- `GET /api/sources/health`

## Query Semantics
- `window_hours` filters active feed window (default 24).
- `saved=all|true|false`:
  - `true`: saved view (no time cutoff applied).
  - `all`/`false`: applies time cutoff.
- Ordered by `published_at_utc DESC`, then `updated_at_utc DESC`.

## Persistence Rules
- Save/unsave mutates only `is_saved` flag.
- Saved articles persist until explicitly unsaved and later removed by retention.
