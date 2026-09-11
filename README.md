# Screener 500 — public data bundle

Static JSON consumed by the Screener 500 app. Regenerated once per trading day from the research
engine (sanitized: no portfolio, positions, P&L, sizing or book-relative gates), plus a delayed
quote file refreshed every 10 minutes during US market hours by the `quotes` workflow.

| File | Refresh | Contents |
|---|---|---|
| `manifest.json` | daily | as_of, counts, schema_version |
| `latest.json` | daily | universe summaries, macro, credit, scan notes, themes |
| `tickers/<T>.json` | daily | full public detail per name |
| `quotes.json` | 10 min (market hours) | delayed price / change per ticker (FMP batch quote) |

Served by GitHub Pages from the `main` branch root. `.nojekyll` disables Jekyll so `tickers/` and
files starting with `_` are served as-is.

## Secrets

The quote workflow reads `FMP_API_KEY` from the repository's Actions secrets. The key is never
stored in this repo.

Not investment advice.
