# Data Retention SOP

## Goal
Keep active unsaved data fresh while retaining user-saved records.

## Rule
- Delete unsaved articles where `published_at_utc < now_utc - 24h`.
- Never delete records with `is_saved = 1` during retention cleanup.

## Trigger
- Run cleanup immediately after each ingestion run.
- Optional standalone cleanup via `tools/cleanup_retention.py`.

## Verification
- Track deleted count and include in ingestion run notes.
- Tests must verify:
  - old unsaved rows removed,
  - old saved rows retained.
