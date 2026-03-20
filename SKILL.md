---
name: wallapop-scraper
description: Run live searches against Wallapop and return structured marketplace results. Use when an AI agent needs to search Wallapop listings, apply filters such as query, price, category, or location, and return clean JSON or a concise summary. Use this skill instead of scraping HTML manually when the task is "search Wallapop", "find listings on Wallapop", "collect marketplace results", or "get current Wallapop items for a query".
---

# Wallapop Scraper

Use the bundled script for deterministic agent-friendly runs.

## Quick Start

Run:

```bash
python3 scripts/search_wallapop.py --query "bmw e36" --max-results 10
```

Return JSON:

```bash
python3 scripts/search_wallapop.py --query "golf gti" --max-results 20 --json
```

## Workflow

1. Prefer `scripts/search_wallapop.py` over calling Playwright manually.
2. Pass filters through flags instead of editing code.
3. Use `--json` when another tool or agent needs structured output.
4. Use `--headed` only when debugging browser behavior.
5. Summarize the results instead of pasting long raw output unless the user asked for JSON.

## Flags

- `--query`: Search keywords.
- `--category-id`: Wallapop category ID.
- `--min-price`: Minimum price in EUR.
- `--max-price`: Maximum price in EUR.
- `--latitude`: Latitude filter.
- `--longitude`: Longitude filter.
- `--distance-km`: Radius filter in kilometers.
- `--order-by`: Sort order.
- `--max-results`: Maximum number of results to return.
- `--json`: Print JSON only.
- `--headed`: Run with a visible browser window.

## Implementation Notes

- The wrapper script calls `wallapop_scraper.py` with `--quiet` so JSON mode stays clean.
- The scraper uses Playwright and Wallapop's current API responses captured from the live page.
- If Playwright is missing, install dependencies from `requirements.txt` and run `playwright install chromium`.
