# Findings

## Snapshot
- Date: 2026-02-21
- Workspace: backend-first implementation from empty repository.

## Requirements Locked
- Scope: Backend first; dashboard and Notion integration deferred.
- Sources (v1):
  - Perfect Daily Grind
  - Daily Coffee News
  - Specialty Coffee Association (SCA)
  - Barista Magazine
  - Tea & Coffee Trade Journal
- Window: rolling 24 hours in UTC.
- Deduplication: canonical URL.
- Persistence: SQLite.
- Saved state: global and persistent.
- Retention: unsaved items expire outside active window; saved items persist.

## Source Research and Endpoint Strategy
- Implementation uses RSS/API-first ingestion with scraper fallback.
- Default feed assumptions (configurable in code):
  - `https://perfectdailygrind.com/feed/`
  - `https://dailycoffeenews.com/feed/`
  - `https://sca.coffee/rss` (fallback listing used if unavailable)
  - `https://www.baristamagazine.com/feed/`
  - `https://www.teaandcoffee.net/feed/`
- Listing-page fallbacks are configured per source to continue ingestion when feeds fail or are unavailable.

## Environmental Constraint Discovered
- Network/DNS is not available in this sandbox runtime.
- Consequence: live endpoint reachability and external source handshake cannot be fully validated here.
- Mitigation: deterministic `tools/verify_links.py` and `GET /api/sources/health` provide runtime verification in your networked environment.

## Technical Constraints and Safeguards
- No full-text storage; metadata + snippets only.
- Missing/unparseable publish timestamps are skipped and logged as warnings.
- Source-level failures do not abort whole ingestion run; run status becomes `partial_failure` when needed.
- URL canonicalization strips known tracking params and normalizes host/scheme/path.

## Open Items (Deferred)
- Notion sync mapping and delivery adapter.
- Frontend dashboard implementation.
- Cloud deployment and external cron/webhook orchestration.

## External Reference Scan
- FastAPI backend structure references reviewed:
  - https://github.com/gospodima/async-fastapi-sqlalchemy-template
  - https://github.com/Donnype/fastapi-template
  - https://github.com/TimoReusch/FastAPI-project-template
- Feed parsing references reviewed:
  - https://github.com/NicolasLM/atoma
  - https://github.com/kagisearch/fastfeedparser
- Notes:
  - v1 implementation remains stdlib-oriented for feed parsing logic to reduce dependency surface.
  - Source adapters are intentionally configurable because live feed availability differs by environment/runtime.

## Design Asset Findings (2026-02-21)
- Brand logo (`DesignGuideline/222 logo negro.png`) is monochrome and high-contrast; suitable for dark or light surfaces.
- Inspiration image (`DesignGuideline/designinspo.png`) emphasizes card hierarchy, side rail navigation, and strong dashboard rhythm.
- BrandGuidelines constraints applied:
  - palette: black, mint accent, white background
  - typography: Satoshi + Helvetica Neue family
  - rhythm: 4px spacing unit and 8px radius
- Design translation decision:
  - use a light editorial canvas with dark top bar and information cards to retain dashboard depth without copying purple-heavy inspiration.
