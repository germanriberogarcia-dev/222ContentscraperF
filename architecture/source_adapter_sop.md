# Source Adapter SOP

## Goal
Standardize source connectivity with RSS/API-first collection and HTML scrape fallback.

## Adapter Contract
- Input: `Settings`.
- Output: `(articles, warnings)` where `articles` is list of `RawArticle`.

## Required Behavior
1. Attempt feed endpoint when configured.
2. Parse RSS/Atom entries with title, link, publish date, snippet, image.
3. If feed fails/empty and scraper is enabled:
   - Parse listing cards with configured selectors.
   - Enrich missing metadata from article page meta tags (bounded budget).
4. Return deduped article URLs per source fetch.

## Health Handshake
- `check_health` tests feed availability first, then listing fallback.
- Returns deterministic status object (`ok` or `error`) with detail string.

## Constraints
- No full article body storage.
- No secret values in adapter code.
- Request retries/timeouts/user-agent driven by `Settings`.
