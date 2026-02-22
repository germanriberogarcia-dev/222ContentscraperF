# Coffee News Ingestion Backend (B.L.A.S.T. v1)

Local-first FastAPI backend that ingests coffee-industry articles from configured sources, deduplicates by canonical URL, stores in SQLite, and exposes JSON APIs.

## Quick Start

1. Create a virtualenv and install dependencies:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
2. Create env file:
   - `cp .env.example .env`
3. Start backend (scheduler starts automatically):
   - `python -m app.main`
4. Open dashboard screen:
   - `http://localhost:8000/dashboard`

## API

- `GET /api/articles`
- `DELETE /api/articles/{article_id}`
- `POST /api/articles/{article_id}/save`
- `DELETE /api/articles/{article_id}/save`
- `POST /api/ingestion/run`
- `GET /api/ingestion/status`
- `GET /api/sources/health`

## Dashboard Screen

- Route: `GET /dashboard`
- Static assets route: `GET /dashboard-assets/*`

## Deterministic Tools

- `python tools/verify_links.py`
- `python tools/run_ingestion.py`
- `python tools/cleanup_retention.py`
- `python tools/health_report.py`
