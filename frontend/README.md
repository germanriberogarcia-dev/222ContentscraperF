# Frontend Design Mock

Open `frontend/scrape_dashboard_profile.html` in a browser to preview the brand-aligned scrape dashboard profile.

Behavior:
- If backend API is running, the page consumes live endpoints under `/api/*`.
- If backend API is unavailable, the page renders built-in demo article cards.
- Saved articles persist in browser `localStorage` with key `ag222_saved_articles`.
