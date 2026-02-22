# Gemini Constitution

## Project Constitution
- Status: `Active - Backend v1 Implemented`
- Date initialized: 2026-02-21
- Last updated: 2026-02-21

## A.N.T. Architecture Invariants
1. Layer 1 (`architecture/`) is the source of truth for procedure (SOP-first rule).
2. Layer 2 (navigation/decision logic) routes tasks between SOPs and deterministic tools.
3. Layer 3 (`tools/`) contains deterministic, atomic, testable Python scripts.
4. Intermediate artifacts are stored only in `.tmp/`.
5. Environment secrets/config values come from `.env` or process env, never hardcoded.
6. Data mutation flow is deterministic: ingest -> normalize -> dedupe upsert -> retention cleanup.

## Behavioral Rules
- Reliability over speed.
- No guessing at business logic.
- Data-first: schema is locked before tool implementation.
- If logic changes, update SOP docs in `architecture/` first, then update code.
- Skip items with missing/unreliable publish times and record warnings.

## Locked Product Decisions
- Milestone: backend first.
- Sources: 5 publishers, Reddit deferred.
- Ingestion: RSS/API first, scraper fallback.
- Time window: rolling 24h UTC.
- Dedupe key: canonical URL.
- Storage: SQLite.
- Save model: global (no auth in v1).
- Retention: unsaved outside window removed; saved retained.
- Payload: JSON API only.
- Content depth: metadata + snippet only.
- Scheduler: internal daily scheduler + manual trigger endpoint.
- Deployment: local-first.

## Final Data Schemas

### Input Schema
```json
{
  "runtime": {
    "now_utc": "ISO-8601 string",
    "window_hours": 24
  },
  "sources": [
    {
      "id": "string",
      "name": "string",
      "base_url": "string",
      "feed_url": "string|null",
      "listing_url": "string",
      "scraper_enabled": "boolean",
      "active": "boolean"
    }
  ],
  "settings": {
    "db_path": "string",
    "user_agent": "string",
    "request_timeout_seconds": "integer",
    "request_retries": "integer",
    "schedule_hour_utc": "integer",
    "schedule_minute_utc": "integer"
  }
}
```

### Output Schema
```json
{
  "status": "success|partial_failure|failed|running",
  "run_id": "string",
  "timestamp_utc": "ISO-8601 string",
  "payload": {
    "articles": [
      {
        "id": "string",
        "source_id": "string",
        "source_name": "string",
        "title": "string",
        "url": "string",
        "canonical_url": "string",
        "published_at_utc": "ISO-8601 string",
        "snippet": "string",
        "image_url": "string|null",
        "is_saved": "boolean",
        "first_seen_at_utc": "ISO-8601 string",
        "last_seen_at_utc": "ISO-8601 string"
      }
    ]
  },
  "metrics": {
    "records_in": "number",
    "records_out": "number",
    "new_count": "number",
    "updated_count": "number",
    "skipped_count": "number",
    "error_count": "number"
  },
  "trace": {
    "sop_version": "string",
    "tools_used": ["string"],
    "warnings": ["string"]
  }
}
```

## Change Control
Update this file only when:
- A schema changes.
- A rule is added or revised.
- Architecture invariants are modified.

## Maintenance Log
- 2026-02-21: Constitution initialized with draft schemas and execution gates.
- 2026-02-21: Backend v1 schema locked and implementation constraints finalized.
- 2026-02-21: Added local-first runbook assumptions and deferred items (Notion/UI/cloud trigger).
