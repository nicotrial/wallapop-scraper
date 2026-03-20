# wallapop-scraper

Playwright-based Wallapop scraper with a CLI for live marketplace searches.

## Setup

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/playwright install chromium
```

## Usage

```bash
./venv/bin/python wallapop_scraper.py --query "bmw e36" --max-results 20
./venv/bin/python wallapop_scraper.py --query "golf gti" --min-price 1000 --max-price 8000 --json
./venv/bin/python wallapop_scraper.py --query "bmw e36" --headed
```

## Options

```bash
./venv/bin/python wallapop_scraper.py --help
```
