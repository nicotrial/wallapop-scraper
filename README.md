# wallapop-scraper

Playwright-based Wallapop scraper with a simple CLI.

## Setup

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/playwright install chromium
```

## Usage

```bash
./venv/bin/python wallapop_scraper.py --query "bmw e36" --max-results 20
./venv/bin/python wallapop_scraper.py --query "golf gti" --max-results 50 --json
```
