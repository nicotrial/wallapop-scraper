#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any

import httpx
from openai import OpenAI

MAX_TOOL_CALLS_PER_TURN = 4
SEARCH_CACHE: dict[str, dict[str, Any]] = {}
CATEGORY_CACHE_TTL_SECONDS = 24 * 60 * 60
MAX_ITEMS_RETURNED_TO_MODEL = 8
CATEGORY_QUERY_ALIASES = {
    "car": ["cars"],
    "cars": ["cars"],
    "coche": ["coches", "coche"],
    "coches": ["coches", "coche"],
    "motorcycle": ["motorbike", "motorbikes"],
    "motorcycles": ["motorbike", "motorbikes"],
    "motorbike": ["motorbike", "motorbikes"],
    "motorbikes": ["motorbike", "motorbikes"],
    "moto": ["motos", "moto", "motocicleta", "motocicletas"],
    "motos": ["motos", "moto", "motocicleta", "motocicletas"],
    "motocicleta": ["motos", "moto", "motocicleta", "motocicletas"],
    "motocicletas": ["motos", "moto", "motocicleta", "motocicletas"],
    "bike": ["bicycle", "bicycles"],
    "bikes": ["bicycle", "bicycles"],
    "bicicleta": ["bicicletas", "bicicleta"],
    "bicicletas": ["bicicletas", "bicicleta"],
    "phone": ["mobile phone", "mobile phones"],
    "phones": ["mobile phone", "mobile phones"],
    "movil": ["moviles", "movil", "telefono", "telefonos"],
    "móviles": ["moviles", "movil", "telefono", "telefonos"],
    "telefono": ["telefono", "telefonos", "movil", "moviles"],
    "teléfono": ["telefono", "telefonos", "movil", "moviles"],
    "computer": ["computers"],
    "computers": ["computers"],
    "ordenador": ["ordenadores", "ordenador"],
    "ordenadores": ["ordenadores", "ordenador"],
    "furniture": ["furniture"],
    "mueble": ["muebles", "mueble"],
    "muebles": ["muebles", "mueble"],
    "sofa": ["sofas", "furniture"],
    "sofa": ["sofas", "muebles"],
    "sofá": ["sofas", "muebles"],
    "motorcycle parts": ["motorbike and four-wheeler spare parts", "motorbike spare parts", "motorbike accessories", "motorbike"],
    "car parts": ["car & van spare parts", "car spare parts", "car accessories", "cars"],
    "piezas de moto": ["motor y accesorios", "repuestos de moto", "motos"],
    "recambios de moto": ["motor y accesorios", "repuestos de moto", "motos"],
    "piezas de coche": ["recambios de coches y furgonetas", "repuestos para coches y furgonetas", "coches"],
    "piezas de coches": ["recambios de coches y furgonetas", "repuestos para coches y furgonetas", "coches"],
    "recambios de coche": ["recambios de coches y furgonetas", "repuestos para coches y furgonetas", "coches"],
    "recambios de coches": ["recambios de coches y furgonetas", "repuestos para coches y furgonetas", "coches"],
    "moto custom": ["motos", "custom", "chopper"],
    "moto clasica": ["motos", "clasicas", "clasica"],
    "mtb": ["bicicletas", "bicicleta montaña", "bici montaña", "bicicletas y triciclos"],
    "bici montaña": ["bicicletas", "bicicleta montaña", "bicicletas y triciclos"],
    "bicicleta montaña": ["bicicletas", "bicicleta montaña", "bicicletas y triciclos"],
}

COMMON_EXCLUDE_TERMS = {
    "bike_complete": [
        "horquilla",
        "pedales",
        "ruedas",
        "llantas",
        "cubiertas",
        "cubierta",
        "neumaticos",
        "neumáticos",
        "cámara",
        "camara",
        "sillin",
        "sillín",
        "manillar",
        "puños",
        "punos",
        "freno",
        "frenos",
        "cassette",
        "desviador",
        "plato",
        "bielas",
        "cadena",
        "portabicicletas",
        "botas",
        "maillot",
        "casco",
    ],
    "moto_complete": [
        "casco",
        "chaqueta",
        "guantes",
        "botas",
        "escape",
        "motor",
        "despiece",
        "despiezo",
        "llanta",
        "llantas",
        "neumatico",
        "neumático",
        "faro",
        "faro delantero",
        "intermitente",
    ],
}
COMPLETE_VEHICLE_PROFILES = {"bike_complete", "moto_complete", "car_complete"}
AGENT_BANNER = r"""
__        __    _ _                         _
\ \      / /_ _| | | __ _ _ __   ___  _ __| |
 \ \ /\ / / _` | | |/ _` | '_ \ / _ \| '__| |
  \ V  V / (_| | | | (_| | |_) | (_) | |  | |
   \_/\_/ \__,_|_|_|\__,_| .__/ \___/|_|  |_|
                         |_|

    AI Buying Assistant for Wallapop
"""


def resolve_client_config() -> tuple[str | None, str, str]:
    explicit_base_url = os.getenv("AI_BASE_URL")
    ai_api_key = os.getenv("AI_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    nvidia_api_key = os.getenv("NVIDIA_API_KEY")

    if explicit_base_url:
        api_key = ai_api_key or openai_api_key or nvidia_api_key
        if not api_key:
            raise RuntimeError("Set AI_API_KEY, OPENAI_API_KEY, or NVIDIA_API_KEY before running this script.")
        model = os.getenv("AI_MODEL") or os.getenv("NVIDIA_MODEL") or "gpt-4.1-mini"
        return explicit_base_url, api_key, model

    if nvidia_api_key and not openai_api_key and not ai_api_key:
        model = os.getenv("NVIDIA_MODEL") or "nvidia/nemotron-3-super-120b-a12b"
        return "https://integrate.api.nvidia.com/v1", nvidia_api_key, model

    api_key = ai_api_key or openai_api_key
    if not api_key:
        raise RuntimeError("Set AI_API_KEY, OPENAI_API_KEY, or NVIDIA_API_KEY before running this script.")

    model = os.getenv("AI_MODEL") or "gpt-4.1-mini"
    return None, api_key, model


def build_client() -> OpenAI:
    base_url, api_key, _ = resolve_client_config()
    if base_url:
        return OpenAI(base_url=base_url, api_key=api_key)
    return OpenAI(api_key=api_key)


def get_category_cache_path() -> Path:
    return Path(__file__).resolve().parent / ".wallapop_categories_cache.json"


def load_cached_categories() -> list[dict[str, Any]] | None:
    cache_path = get_category_cache_path()
    if not cache_path.exists():
        return None

    try:
        payload = json.loads(cache_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None

    fetched_at = payload.get("fetched_at")
    categories = payload.get("categories")
    locale = payload.get("locale")
    if not isinstance(fetched_at, (int, float)) or not isinstance(categories, list) or locale != "es":
        return None

    if time.time() - fetched_at > CATEGORY_CACHE_TTL_SECONDS:
        return None
    return categories


def save_cached_categories(categories: list[dict[str, Any]]):
    cache_path = get_category_cache_path()
    payload = {
        "fetched_at": time.time(),
        "locale": "es",
        "categories": categories,
    }
    cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))


def fetch_wallapop_categories(force_refresh: bool = False) -> list[dict[str, Any]]:
    if not force_refresh:
        cached = load_cached_categories()
        if cached is not None:
            return cached

    response = httpx.get(
        "https://api.wallapop.com/api/v3/categories",
        headers={"Accept-Language": "es-ES,es;q=0.9"},
        timeout=30.0,
    )
    response.raise_for_status()
    payload = response.json()
    categories = payload.get("categories", [])
    if not isinstance(categories, list):
        raise RuntimeError("Unexpected categories payload from Wallapop.")
    save_cached_categories(categories)
    return categories


def flatten_categories(categories: list[dict[str, Any]], parents: list[str] | None = None) -> list[dict[str, Any]]:
    parents = parents or []
    flattened: list[dict[str, Any]] = []

    for category in categories:
        name = category.get("name", "")
        path_parts = [*parents, name] if name else [*parents]
        flattened.append(
            {
                "id": category.get("id"),
                "name": name,
                "path": " > ".join(path_parts),
                "vertical_id": category.get("vertical_id"),
                "leaf_selection_mandatory": category.get("category_leaf_selection_mandatory", False),
            }
        )

        subcategories = category.get("subcategories") or []
        if isinstance(subcategories, list) and subcategories:
            flattened.extend(flatten_categories(subcategories, path_parts))

    return flattened


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def tokenize(text: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", normalize_text(text)) if token]


def expand_category_query(query: str) -> list[str]:
    expanded = [query]
    normalized = normalize_text(query.strip())
    if normalized in CATEGORY_QUERY_ALIASES:
        expanded.extend(CATEGORY_QUERY_ALIASES[normalized])
    return list(dict.fromkeys(item for item in expanded if item))


def find_wallapop_categories(arguments: dict[str, Any]) -> dict[str, Any]:
    query = (arguments.get("query") or "").strip()
    if not query:
        return {"ok": False, "error": "Category lookup requires a non-empty query."}

    limit = max(1, min(int(arguments.get("limit", 8)), 20))
    categories = flatten_categories(fetch_wallapop_categories(force_refresh=bool(arguments.get("refresh"))))
    query_variants = expand_category_query(query)
    query_tokens = []
    for variant in query_variants:
        query_tokens.extend(tokenize(variant))

    scored: list[tuple[int, dict[str, Any]]] = []
    for category in categories:
        name = str(category.get("name", ""))
        path = str(category.get("path", ""))
        haystack = normalize_text(f"{name} {path}")
        name_lower = normalize_text(name)
        score = 0

        for variant in query_variants:
            variant_lower = normalize_text(variant)
            if variant_lower == name_lower:
                score += 100
            if variant_lower in name_lower:
                score += 40
            if variant_lower in haystack:
                score += 20

        for token in query_tokens:
            if token == name_lower:
                score += 25
            elif token in name_lower:
                score += 15
            elif token in haystack:
                score += 5

        if score > 0:
            scored.append((score, category))

    scored.sort(key=lambda item: (-item[0], item[1]["path"]))
    matches = [category for _, category in scored[:limit]]
    return {"ok": True, "query": query, "count": len(matches), "categories": matches}


def normalize_search_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    subcategory_ids = arguments.get("subcategory_ids") or []
    if isinstance(subcategory_ids, list):
        normalized_subcategory_ids = sorted(int(value) for value in subcategory_ids)
    else:
        normalized_subcategory_ids = []

    return {
        "query": arguments.get("query", "").strip().lower(),
        "category_id": arguments.get("category_id"),
        "subcategory_ids": normalized_subcategory_ids,
        "min_price": arguments.get("min_price"),
        "max_price": arguments.get("max_price"),
        "latitude": arguments.get("latitude"),
        "longitude": arguments.get("longitude"),
        "distance_km": arguments.get("distance_km"),
        "order_by": arguments.get("order_by"),
        "max_results": arguments.get("max_results", 10),
        "headed": bool(arguments.get("headed")),
    }


def make_search_cache_key(arguments: dict[str, Any]) -> str:
    return json.dumps(normalize_search_arguments(arguments), sort_keys=True, ensure_ascii=False)


def run_wallapop_search(arguments: dict[str, Any]) -> dict[str, Any]:
    cache_key = make_search_cache_key(arguments)
    cached = SEARCH_CACHE.get(cache_key)
    if cached is not None:
        cached_result = dict(cached)
        cached_result["cached"] = True
        return cached_result

    repo_root = Path(__file__).resolve().parent
    wrapper = repo_root / "scripts" / "search_wallapop.py"
    effective_order_by = arguments.get("order_by")
    exclude_profile = arguments.get("exclude_profile")

    # Cheapest-first sorting is very noisy for complete vehicles on Wallapop because
    # it tends to surface parts, rentals, broken items, and low-quality junk first.
    if exclude_profile in COMPLETE_VEHICLE_PROFILES and effective_order_by == "price_low":
        effective_order_by = "newest"

    cmd = [
        sys.executable,
        str(wrapper),
        "--json",
        "--query",
        arguments["query"],
        "--max-results",
        str(arguments.get("max_results", 10)),
    ]

    optional_flags = [
        ("category_id", "--category-id"),
        ("min_price", "--min-price"),
        ("max_price", "--max-price"),
        ("latitude", "--latitude"),
        ("longitude", "--longitude"),
        ("distance_km", "--distance-km"),
    ]

    for key, flag in optional_flags:
        value = arguments.get(key)
        if value is not None:
            cmd.extend([flag, str(value)])

    subcategory_ids = arguments.get("subcategory_ids") or []
    if isinstance(subcategory_ids, list):
        for subcategory_id in subcategory_ids:
            cmd.extend(["--subcategory-id", str(subcategory_id)])

    if effective_order_by is not None:
        cmd.extend(["--order-by", str(effective_order_by)])

    if arguments.get("headed"):
        cmd.append("--headed")

    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)

    if result.returncode != 0:
        return {
            "ok": False,
            "error": "Wallapop search command failed.",
            "stderr": result.stderr.strip(),
            "stdout": result.stdout.strip(),
            "command": cmd,
        }

    try:
        items = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "error": "Wallapop search did not return valid JSON.",
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "command": cmd,
        }

    exclude_terms = [normalize_text(term) for term in arguments.get("exclude_terms", [])]
    if exclude_profile in COMMON_EXCLUDE_TERMS:
        exclude_terms.extend(normalize_text(term) for term in COMMON_EXCLUDE_TERMS[exclude_profile])

    if exclude_terms:
        filtered_items = []
        removed_items = []
        for item in items:
            haystack = normalize_text(f"{item.get('title', '')} {item.get('description', '')}")
            if any(term in haystack for term in exclude_terms):
                removed_items.append(item)
                continue
            filtered_items.append(item)
        items = filtered_items
    else:
        removed_items = []

    trimmed_items = items[:MAX_ITEMS_RETURNED_TO_MODEL]

    response = {
        "ok": True,
        "query": arguments["query"],
        "filters": {
            "category_id": arguments.get("category_id"),
            "min_price": arguments.get("min_price"),
            "max_price": arguments.get("max_price"),
            "latitude": arguments.get("latitude"),
            "longitude": arguments.get("longitude"),
            "distance_km": arguments.get("distance_km"),
            "order_by": effective_order_by,
            "max_results": arguments.get("max_results", 10),
        },
        "count": len(items),
        "items": trimmed_items,
        "returned_to_model": len(trimmed_items),
        "removed_count": len(removed_items),
    }
    SEARCH_CACHE[cache_key] = response
    return response


def get_wallapop_listing_details(arguments: dict[str, Any]) -> dict[str, Any]:
    url = (arguments.get("url") or "").strip()
    if not url:
        return {"ok": False, "error": "Listing detail lookup requires a non-empty url."}

    try:
        response = httpx.get(
            url,
            headers={
                "Accept-Language": "es-ES,es;q=0.9",
                "User-Agent": "Mozilla/5.0",
            },
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return {"ok": False, "error": f"Failed to fetch listing page: {exc}"}

    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', response.text)
    if not match:
        return {"ok": False, "error": "Could not find listing page data."}

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {"ok": False, "error": "Could not parse listing page data."}

    page_props = data.get("props", {}).get("pageProps", {})
    item = page_props.get("item", {})
    seller = page_props.get("itemSeller", {})

    details = {
        "ok": True,
        "url": url,
        "id": item.get("id"),
        "title": item.get("title", {}).get("original"),
        "description": item.get("description", {}).get("original"),
        "condition": item.get("characteristics"),
        "price": item.get("salePrice"),
        "currency": item.get("currency"),
        "taxonomies": [
            {
                "id": taxonomy.get("id"),
                "name": taxonomy.get("name"),
            }
            for taxonomy in item.get("taxonomies", [])
        ],
        "seller": {
            "id": seller.get("id"),
            "name": seller.get("microName"),
            "web_slug": seller.get("webSlug"),
        },
        "modified_date": item.get("modifiedDate"),
        "share_url": item.get("shareUrl"),
    }

    return details


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_wallapop_listings",
            "description": (
                "Search Wallapop listings with the local scraper. Use this whenever the user asks "
                "for current marketplace results, specific vehicles, a budget, location, or filters "
                "such as 'no parts', 'drivable', 'project car', or multiple models. "
                "Use a real category_id when it materially improves result quality. "
                "If you are not confident about the category_id for a product type, call the category lookup tool first. "
                "If the user's intent is still vague, ask clarifying questions first instead of calling the tool immediately. "
                "Call this tool one or more times once you have enough information to search usefully. "
                "Wallapop is Spanish, so prefer Spanish search queries unless the user gives a specific brand or model."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keywords to send to Wallapop, such as 'mazda rx7' or 'corvette'.",
                    },
                    "category_id": {
                        "type": "integer",
                        "description": "Wallapop category ID. Use 100 for cars when the user is looking for vehicles.",
                    },
                    "subcategory_ids": {
                        "type": "array",
                        "description": "Optional Wallapop subcategory IDs to narrow the search when the agent knows the precise subcategory.",
                        "items": {"type": "integer"},
                    },
                    "min_price": {
                        "type": "integer",
                        "description": "Minimum price in EUR.",
                    },
                    "max_price": {
                        "type": "integer",
                        "description": "Maximum price in EUR.",
                    },
                    "latitude": {
                        "type": "number",
                        "description": "Latitude filter when location is known.",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude filter when location is known.",
                    },
                    "distance_km": {
                        "type": "integer",
                        "description": "Search radius in kilometers.",
                    },
                    "order_by": {
                        "type": "string",
                        "description": "Sort order.",
                        "enum": ["newest", "price_low", "price_high", "closest"],
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "How many results to return.",
                    },
                    "headed": {
                        "type": "boolean",
                        "description": "Run browser visibly for debugging only.",
                    },
                    "exclude_terms": {
                        "type": "array",
                        "description": "Words that should exclude obvious mismatches from the returned results.",
                        "items": {"type": "string"},
                    },
                    "exclude_profile": {
                        "type": "string",
                        "description": "Built-in mismatch filter profile for common product types.",
                        "enum": ["bike_complete", "moto_complete", "car_complete"],
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_wallapop_categories",
            "description": (
                "Look up Wallapop category IDs from the live categories endpoint with local caching. "
                "Use this when you need the correct category_id for a product type such as moto, coche, recambios, bicicletas, móviles, or muebles, "
                "instead of guessing category IDs from memory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Category name or product type to look up, such as 'moto', 'coches', or 'recambios de coche'.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of category matches to return.",
                    },
                    "refresh": {
                        "type": "boolean",
                        "description": "Refresh the categories cache from Wallapop.",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_wallapop_listing_details",
            "description": (
                "Fetch the full Wallapop listing page and extract the structured detail data from the live page. "
                "Use this on promising listings before recommending them, especially when you need to verify condition, "
                "full description, taxonomy, or other details that may not be obvious from search snippets."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full Wallapop listing URL.",
                    }
                },
                "required": ["url"],
                "additionalProperties": False,
            },
        },
    },
]

TOOL_IMPLS = {
    "search_wallapop_listings": run_wallapop_search,
    "find_wallapop_categories": find_wallapop_categories,
    "get_wallapop_listing_details": get_wallapop_listing_details,
}

SYSTEM_PROMPT = (
    "You are a sharp, practical Wallapop buying assistant. "
    "Wallapop is a Spanish marketplace. Think in Spanish first for category names and search queries, unless the product name, brand, or model is better kept in another language. "
    "Reply in the user's language. If the user writes in Spanish, answer in Spanish. "
    "Your job is to help the user find the best listing for their actual goal, not to dump search output. "
    "Be proactive, selective, and useful. Interpret vague requests, infer sensible filters, and guide the user toward the strongest options. "
    "Think like an experienced private-buyer advisor: compare options, spot red flags, explain tradeoffs, and recommend what you would shortlist. "
    "Start by understanding the buyer. If the request is not specific enough, ask a few short clarifying questions before using tools. "
    "Clarify things like budget, type of vehicle, use case, location, transmission, condition, style, mileage tolerance, or deal-breakers when they matter. "
    "Do not rush into tool use when the user's goal is still vague. "
    "If the user is already clear enough, skip questions and search directly. "
    "Ask at most 1 or 2 short follow-up questions at a time, not long questionnaires. "
    "Do not guess category or subcategory IDs from memory for unfamiliar product types. Use the category lookup tool when needed. "
    "Use the search tool whenever the user asks for current Wallapop listings or wants recommendations "
    "based on live inventory. "
    "Prefer category_id=100 when the user wants cars, project cars, or drivable vehicles. "
    "If the user mentions multiple candidate cars, run separate searches when that produces better results. "
    "Filter out obvious mismatches such as parts, shells, engines, or non-drivable listings when the user asks "
    "for complete or drivable cars. "
    "Use title and description to judge relevance, and explain why shortlisted listings match or fail the user's criteria. "
    "Do not invent listings. If results are weak, say so and suggest a refined search. "
    "Never speculate about Wallapop indexing, hidden categories, or broken filters as if they were facts. "
    "If a search returns no useful results, say that clearly, then either try one better-targeted search or ask one focused follow-up question. "
    "For complete vehicles, do not default to sorting by lowest price, because that often surfaces parts and junk. "
    "Prefer Wallapop's default relevance or newest listings, then apply budget and content filtering. "
    "When the user says a result set is not good enough, adapt the next search directly instead of repeating previous conclusions. "
    "When the user explicitly says to use the tool, search immediately and then answer with a concrete shortlist or a clear 'no aparecen resultados buenos'. "
    "If you search by several brands and none returns good matches, say that directly and propose the nearest acceptable fallback instead of drifting. "
    "Do not reuse urban/city bike suggestions when the user asked for mountain use. "
    "If the user asks for something modern, prioritize bikes that look newer, are from modern mass-market lines, or are described as current/recent; avoid presenting obviously outdated models as ideal picks unless budget leaves no better option. "
    "Use subcategories when the product type is specific enough, for example MTB instead of generic Bicicletas. "
    "Before strongly recommending a listing, inspect the listing detail page when possible instead of relying only on the short search snippet. "
    "Do not just dump raw search results. Shortlist the best options, rank them, explain why you chose them, "
    "call out red flags, and include the direct Wallapop URL for every recommended listing. "
    "When you include a listing URL, copy the exact url field from the tool output. Never rewrite the domain, slug, or path. "
    "When the user asks for something like a nice project or a drivable vehicle, infer practical filters from the text and exclude obvious mismatches. "
    "For complete bikes or complete motorcycles, use result filtering to remove parts, accessories, clothing, and obvious non-vehicle listings. "
    "Prefer compact bullet lists over markdown tables so the answer is easier to read in a terminal and less likely to be truncated. "
    "When possible, end with a concrete recommendation such as best pick, safest pick, or best value. "
    "If the user is undecided, help them narrow the search instead of staying neutral. "
    "Treat this as an interactive back-and-forth shopping session: ask, search, refine, compare, and search again until the user finds something they like. "
    "After showing options, invite the next decision, such as broadening the budget, changing model, tightening requirements, or comparing two listings. "
    f"Do not spam searches. Use at most {MAX_TOOL_CALLS_PER_TURN} tool calls in one turn. "
    "Avoid near-duplicate searches. Once you have enough evidence, stop searching and give the user a recommendation or ask one focused follow-up question."
)


def stream_model_message(client: OpenAI, conversation: list[dict[str, Any]], model: str) -> dict[str, Any]:
    stream = client.chat.completions.create(
        model=model,
        messages=conversation,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.2,
        top_p=0.7,
        max_tokens=2200,
        stream=True,
    )

    content_parts: list[str] = []
    tool_calls: dict[int, dict[str, Any]] = {}
    printed_prefix = False

    for chunk in stream:
        choices = getattr(chunk, "choices", None) or []
        if not choices:
            continue

        choice = choices[0]
        delta = choice.delta
        if delta is None:
            continue

        delta_content = getattr(delta, "content", None)
        if delta_content:
            if not printed_prefix:
                print("\nAgent: ", end="", flush=True)
                printed_prefix = True
            if isinstance(delta_content, str):
                print(delta_content, end="", flush=True)
                content_parts.append(delta_content)
            else:
                for part in delta_content:
                    text = getattr(part, "text", None)
                    if text:
                        print(text, end="", flush=True)
                        content_parts.append(text)

        for tool_delta in getattr(delta, "tool_calls", None) or []:
            entry = tool_calls.setdefault(
                tool_delta.index,
                {
                    "id": "",
                    "type": "function",
                    "function": {"name": "", "arguments": ""},
                },
            )

            if getattr(tool_delta, "id", None):
                entry["id"] = tool_delta.id

            function = getattr(tool_delta, "function", None)
            if function is not None:
                if getattr(function, "name", None):
                    entry["function"]["name"] += function.name
                if getattr(function, "arguments", None):
                    entry["function"]["arguments"] += function.arguments

    if printed_prefix:
        print()

    ordered_tool_calls = [tool_calls[index] for index in sorted(tool_calls)]
    return {
        "content": "".join(content_parts),
        "tool_calls": ordered_tool_calls,
    }


def normalize_output_text(text: str) -> str:
    """Fix common URL hallucinations in model output."""
    normalized = re.sub(r"https?://(?:www\.)?wallop\.com", "https://wallapop.com", text, flags=re.IGNORECASE)
    normalized = re.sub(r"https?://es\.wallop\.com", "https://es.wallapop.com", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bwallop\.com\b", "wallapop.com", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bes\.wallop\.com\b", "es.wallapop.com", normalized, flags=re.IGNORECASE)
    return normalized


def run_agent_turn(client: OpenAI, conversation: list[dict[str, Any]]) -> str:
    _, _, model = resolve_client_config()
    tool_calls_this_turn = 0
    while True:
        message = stream_model_message(client, conversation, model)
        tool_calls = message["tool_calls"]

        if tool_calls:
            conversation.append(
                {
                    "role": "assistant",
                    "content": message["content"],
                    "tool_calls": tool_calls,
                }
            )

            remaining_budget = MAX_TOOL_CALLS_PER_TURN - tool_calls_this_turn
            executable_tool_calls = tool_calls[: max(remaining_budget, 0)]
            skipped_tool_calls = tool_calls[len(executable_tool_calls):]

            for tool_call in executable_tool_calls:
                tool_name = tool_call["function"]["name"]
                raw_arguments = tool_call["function"]["arguments"] or "{}"
                print(f"[tool] {tool_name}({raw_arguments})")

                try:
                    arguments = json.loads(raw_arguments)
                except json.JSONDecodeError:
                    result = {"ok": False, "error": f"Invalid JSON arguments for {tool_name}."}
                else:
                    handler = TOOL_IMPLS.get(tool_name)
                    if handler is None:
                        result = {"ok": False, "error": f"Unknown tool: {tool_name}"}
                    else:
                        result = handler(arguments)

                if tool_name == "search_wallapop_listings":
                    if result.get("ok"):
                        print(
                            f"[tool-result] {result.get('count', 0)} resultados "
                            f"({result.get('removed_count', 0)} descartados, {result.get('returned_to_model', 0)} enviados al modelo)"
                        )
                    else:
                        print(f"[tool-result] error: {result.get('error')}")
                elif tool_name == "find_wallapop_categories":
                    if result.get("ok"):
                        print(f"[tool-result] {result.get('count', 0)} categorías encontradas")
                    else:
                        print(f"[tool-result] error: {result.get('error')}")
                elif tool_name == "get_wallapop_listing_details":
                    if result.get("ok"):
                        print(f"[tool-result] detalle cargado: {result.get('title')}")
                    else:
                        print(f"[tool-result] error: {result.get('error')}")

                conversation.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(result),
                    }
                )
                tool_calls_this_turn += 1

            for tool_call in skipped_tool_calls:
                conversation.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(
                            {
                                "ok": False,
                                "error": (
                                    f"Search budget exhausted for this turn after {MAX_TOOL_CALLS_PER_TURN} tool calls. "
                                    "Summarize the best options found so far or ask one focused follow-up question instead of searching again."
                                ),
                            }
                        ),
                    }
                )

            continue

        final_text = normalize_output_text((message["content"] or "").strip())
        conversation.append({"role": "assistant", "content": final_text})
        return final_text


def main():
    _, _, model = resolve_client_config()
    client = build_client()
    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]

    print(AGENT_BANNER)
    print(f"Agent ready with model: {model}")
    print("Type 'exit' or 'quit' to stop.")

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break

        conversation.append({"role": "user", "content": user_input})
        run_agent_turn(client, conversation)


if __name__ == "__main__":
    main()
