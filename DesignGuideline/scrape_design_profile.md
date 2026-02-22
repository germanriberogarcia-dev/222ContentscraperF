# 222 Scrape Design Profile

## Identity
- Brand: 222 Traditional Colombian Coffee
- Product surface: Article ingestion dashboard (scraper + curation)
- Audience: Coffee enthusiasts and connoisseurs
- Tone: Modern, editorial, precise
- Energy: Medium

## Visual Direction
- Direction name: Nocturne Mint Editorial Grid
- Mood: Confident, modern, immersive
- Contrast model: Dark canvas with elevated dark surfaces and mint highlights
- Inspiration mapping:
  - Keep: card-driven hierarchy, fast visual scanning, clear status surfaces
  - Replace: neon purple dominance with brand mint and layered neutral blacks

## Core Tokens

### Color
- `--color-primary`: `#000000`
- `--color-accent`: `#9bd5b2`
- `--color-bg`: `#000000`
- `--color-text`: `#e6eeea`
- `--color-link`: `#59217f`
- `--color-surface-dark`: `#070a0c`
- `--color-surface-soft`: `#0f1418`
- `--color-border`: `#273137`

### Typography
- Body: `Satoshi Light`, `HelveticaNeueLT Pro 45 Lt`, `Avenir Next`, sans-serif
- Heading: `HelveticaNeueLT Pro 65 Md`, `Helvetica Neue`, `Futura`, sans-serif
- Sizes:
  - `h1`: `32px`
  - `h2`: `16px`
  - `body`: `14px`

### Spacing and Shape
- Base unit: `4px`
- Radius: `8px`
- Scale: `4, 8, 12, 16, 20, 24, 32`

## Component Rules

### Top Bar
- Left: brand block with monochrome logo on a white top bar for logo legibility.
- Right: run status chip, last sync time, refresh action.

### Source Filter Rail
- Source chips with active/inactive state.
- Search field for title and snippet.
- Saved-only toggle.

### Article Cards
- Required fields: source, title, published time, snippet, URL.
- Optional: image hero.
- Persistent save toggle (`is_saved`) with immediate visual feedback.
- Hover behavior: subtle lift and border accent.

### Status Blocks
- Ingestion run card: run status, counts, errors.
- Freshness card: total in current 24h window.
- Save card: total saved.

## Interaction Principles
- Fast scan first, detail second.
- Preserve user intent on refresh by persisting save state.
- Use one primary accent color (`#9bd5b2`) for affordances and highlights.
- Keep motion meaningful:
  - staggered entry for cards
  - focused hover transitions only

## Accessibility Baseline
- Body text minimum: `14px`
- High contrast for status tags and card text
- Visible keyboard focus ring for all controls
- Click targets >= `36px` for save/filter controls

## Data Display Policy
- Show only metadata and snippet in v1.
- No full article text rendering.
- Keep UTC-based freshness labels to align ingestion logic.
