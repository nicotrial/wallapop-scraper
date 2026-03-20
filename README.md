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

Search with category and subcategory:

```bash
./venv/bin/python wallapop_scraper.py --query "bicicleta montaña" --category-id 17000 --subcategory-id 10214 --max-price 200 --max-results 10 --json
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

## AI Agent Console

The repo also includes `agent_console.py`, which connects a chat model to the Wallapop search tool.

It is designed for requests like:

```text
Don't show me parts. I'm looking for a nice project, maybe a Corvette or a Mazda RX-7, under 8000 euros, and it should be drivable.
```

The model can decide when to call the local Wallapop CLI, run one or more searches, and then tailor the answer to the user's intent.

### What tools the agent has

The agent is not limited to one raw search command. It can use:

- `find_wallapop_categories`: look up live category and subcategory IDs from Wallapop
- `search_wallapop_listings`: search listings with query, category, subcategory, price, distance, sorting, and optional noise filters
- `get_wallapop_listing_details`: open a real Wallapop item page and extract structured detail data before recommending a listing

This allows the agent to:

1. Discover the right category/subcategory
2. Search Wallapop
3. Inspect the most promising listings in detail
4. Recommend and refine with the user

### Configure the model API

Set one of these API keys before running:

```bash
export AI_API_KEY=your_key_here
```

Or use the compatible existing names:

```bash
export NVIDIA_API_KEY=your_key_here
export NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
export NVIDIA_MODEL=nvidia/nemotron-3-super-120b-a12b
```

If you are using NVIDIA Nemotron, you can get the API key from the NVIDIA Build page for this model:

`https://build.nvidia.com/nvidia/nemotron-3-super-120b-a12b`

On that page, open the code/deploy section and use the `Generate API Key` / `Get API Key` flow.

Model page:

`https://build.nvidia.com/nvidia/nemotron-3-super-120b-a12b`

Optional generic overrides:

```bash
export AI_BASE_URL=your_model_base_url
export AI_MODEL=your_model_name
```

### Run the console

```bash
./venv/bin/python agent_console.py
```

Example prompt:

```text
Don't show me parts. I'm looking for a nice project, maybe a Corvette or a Mazda RX-7, under 8000 euros, and it should be drivable.
```

Spanish example prompt:

```text
Hola, busco una MTB moderna por menos de 200 euros. Quiero que descartes piezas y bicis infantiles, uses la subcategoría correcta si existe y me recomiendes solo las mejores opciones con enlace.
```

## Category Discovery

Wallapop categories can be discovered live from the API. For example:

```bash
./venv/bin/python scripts/get_wallapop_categories.py mtb --json
./venv/bin/python scripts/get_wallapop_categories.py "moto custom" --json
./venv/bin/python scripts/get_wallapop_categories.py "recambios de coche" --json
```

This is useful because Wallapop often has a top-level category plus a more specific subcategory. For example, a bike search may use:

- `17000` Bicicletas
- `10056` Bicicletas y triciclos
- `10214` MTB

The agent can use those IDs instead of guessing.

## Listing Inspection

Before recommending a listing, the agent can inspect the full item page:

```bash
./venv/bin/python - <<'PY'
from agent_console import get_wallapop_listing_details
result = get_wallapop_listing_details({
    "url": "https://es.wallapop.com/item/bicicleta-btt-trek-3900-talla-m-azul-ruedas-de-26-1243280321"
})
print(result["title"])
print(result["taxonomies"])
PY
```

This helps the agent verify:

- full description
- real taxonomy/subcategory
- condition
- seller info
- listing URL

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
6. Use category discovery before hardcoding IDs.
7. Inspect listing details before making strong recommendations.

### Recommended Agent Command

For structured output, prefer:

```bash
python3 scripts/search_wallapop.py --query "bmw e36" --max-results 10 --json
```

That wrapper automatically prefers `venv/bin/python` and passes `--quiet` so JSON output stays clean.

## CLI Options

- `--query`: Search keywords.
- `--category-id`: Wallapop category ID.
- `--subcategory-id`: Wallapop subcategory ID. Repeat to pass more than one.
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
