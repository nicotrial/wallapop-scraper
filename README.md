# wallapop-scraper

Playwright-based Wallapop scraper with a CLI for live marketplace searches.

This repo can also be used as a Codex-style skill for an AI agent through `SKILL.md` and `scripts/search_wallapop.py`.

No environment variables are required.

## Install

Clone the repo and install dependencies:

```bash
git clone https://github.com/nicotrial/wallapop-scraper.git
cd wallapop-scraper
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/playwright install chromium
```

## CLI Usage

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

## Use With AI Agents

This repo can be used directly by terminal-based AI coding agents such as Codex, Claude Code, OpenCode/OpenHands-style agents, or similar tools that can read files and run shell commands.

### Option 1: Let the agent use the repo directly

Open a new agent session in the repo directory and ask it to use the wrapper script.

Example prompts:

```text
Use the Wallapop scraper in this repo to search for "bmw e36" and return 10 JSON results.
```

```text
Run scripts/search_wallapop.py for query "golf gti" with max price 8000 and summarize the results.
```

### Option 2: Use it as a skill in Codex-style systems

This repo includes:

- `SKILL.md`
- `agents/openai.yaml`
- `scripts/search_wallapop.py`

If your agent supports skill folders, copy this repo or these files into the agent's skills directory under a folder named `wallapop-scraper`.

Example install:

```bash
mkdir -p ~/.codex/skills/wallapop-scraper
cp -R . ~/.codex/skills/wallapop-scraper
```

Then start a new session and invoke the skill by name.

Example prompt:

```text
Use $wallapop-scraper to search Wallapop for "bmw e36" and return 10 JSON results.
```

### Agent Setup Checklist

In a fresh session, the agent should:

1. Clone the repo.
2. Create the virtualenv.
3. Install `requirements.txt`.
4. Run `./venv/bin/playwright install chromium`.
5. Use `python3 scripts/search_wallapop.py ...` for agent-friendly runs.

### Recommended Agent Command

For structured output, prefer:

```bash
python3 scripts/search_wallapop.py --query "bmw e36" --max-results 10 --json
```

That wrapper automatically prefers `venv/bin/python` and passes `--quiet` so JSON output stays clean.

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
- `--quiet`: Suppress scraper progress logs.

## Help

```bash
./venv/bin/python wallapop_scraper.py --help
```
