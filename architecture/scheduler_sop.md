# Scheduler SOP

## Goal
Run ingestion automatically once per UTC day and support manual trigger path.

## Behavior
1. On application startup, initialize scheduler thread if `SCHEDULER_ENABLED=true`.
2. Compute next UTC run from `SCHEDULE_HOUR_UTC` and `SCHEDULE_MINUTE_UTC`.
3. Sleep until next run time.
4. Invoke ingestion callback.
5. Repeat daily.

## Safety Rules
- Scheduler callback and manual trigger share the same non-blocking lock.
- If ingestion is already running, manual endpoint returns conflict (HTTP 409).
- Scheduler errors are logged and do not crash API process.
