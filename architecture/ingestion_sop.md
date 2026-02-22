# Ingestion SOP

## Goal
Deterministically collect recent articles from configured sources and persist normalized records for API delivery.

## Inputs
- Runtime UTC timestamp.
- Source adapter registry.
- Settings (`DB_PATH`, request policy, window hours).

## Deterministic Flow
1. Create ingestion run record with status `running`.
2. For each source adapter:
   - Fetch from feed first.
   - If feed fails/empty and scraper enabled, fetch from listing fallback.
3. For each fetched article:
   - Require publish timestamp.
   - Convert publish time to UTC.
   - Filter to `published_at_utc >= now_utc - 24h`.
   - Canonicalize URL.
   - Upsert by canonical URL.
4. Apply retention cleanup for unsaved records outside active window.
5. Finalize run status:
   - `success` if no source errors.
   - `partial_failure` if some source errors.
   - `failed` if all sources fail.
6. Persist run metrics and warnings in `ingestion_runs.notes`.

## Edge Cases
- Missing publish date: skip article and log warning.
- Duplicate URL across reruns: update existing record, do not duplicate.
- Single-source outage: continue remaining sources.
