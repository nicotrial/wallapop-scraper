# wallapop-scraper

Playwright-based Wallapop scraper with a CLI for live marketplace searches.

This repo can also be used as a Codex-style skill for an AI agent through `SKILL.md` and `scripts/search_wallapop.py`.

No environment variables are required.

## Setup

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/playwright install chromium
```

## Usage

Basic search:

```bash
./venv/bin/python wallapop_scraper.py --query "bmw e36" --max-results 20
```

Price filters:

```bash
./venv/bin/python wallapop_scraper.py --query "golf gti" --min-price 1000 --max-price 8000 --max-results 30
```

JSON output:

```bash
./venv/bin/python wallapop_scraper.py --query "golf gti" --max-results 10 --json
```

Visible browser window:

```bash
./venv/bin/python wallapop_scraper.py --query "bmw e36" --headed
```

Location filters:

```bash
./venv/bin/python wallapop_scraper.py --query "bmw e36" --latitude 40.4168 --longitude -3.7038 --distance-km 50
```

Custom category and sorting:

```bash
./venv/bin/python wallapop_scraper.py --query "mountain bike" --category-id 12465 --order-by newest --max-results 25
```

## Skill Usage

Agent-friendly wrapper:

```bash
python3 scripts/search_wallapop.py --query "bmw e36" --max-results 10 --json
```

Skill files:

- `SKILL.md`: agent instructions and workflow
- `agents/openai.yaml`: UI metadata
- `scripts/search_wallapop.py`: deterministic wrapper that prefers the repo venv

## CLI Options

- `--query`: Search keywords.
- `--category-id`: Wallapop category ID.
- `--min-price`: Minimum price in EUR.
- `--max-price`: Maximum price in EUR.
- `--latitude`: Latitude filter.
- `--longitude`: Longitude filter.
- `--distance-km`: Radius filter in kilometers.
- `--order-by`: Sort order.
- `--max-results`: Maximum number of results to return.
- `--headed`: Open a visible browser instead of headless mode.
- `--json`: Print results as JSON.

## Help

```bash
./venv/bin/python wallapop_scraper.py --help
```
