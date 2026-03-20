#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from openai import OpenAI


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


def run_wallapop_search(arguments: dict[str, Any]) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parent
    wrapper = repo_root / "scripts" / "search_wallapop.py"

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
        ("order_by", "--order-by"),
    ]

    for key, flag in optional_flags:
        value = arguments.get(key)
        if value is not None:
            cmd.extend([flag, str(value)])

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

    return {
        "ok": True,
        "query": arguments["query"],
        "filters": {
            "category_id": arguments.get("category_id"),
            "min_price": arguments.get("min_price"),
            "max_price": arguments.get("max_price"),
            "latitude": arguments.get("latitude"),
            "longitude": arguments.get("longitude"),
            "distance_km": arguments.get("distance_km"),
            "order_by": arguments.get("order_by"),
            "max_results": arguments.get("max_results", 10),
        },
        "count": len(items),
        "items": items,
    }


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_wallapop_listings",
            "description": (
                "Search Wallapop listings with the local scraper. Use this whenever the user asks "
                "for current marketplace results, specific vehicles, a budget, location, or filters "
                "such as 'no parts', 'drivable', 'project car', or multiple models. Call this tool "
                "one or more times before answering listing requests."
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
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    }
]

TOOL_IMPLS = {
    "search_wallapop_listings": run_wallapop_search,
}

SYSTEM_PROMPT = (
    "You are a marketplace assistant for Wallapop. "
    "Use the search tool whenever the user asks for current Wallapop listings or wants recommendations "
    "based on live inventory. "
    "Prefer category_id=100 when the user wants cars, project cars, or drivable vehicles. "
    "If the user mentions multiple candidate cars, run separate searches when that produces better results. "
    "Filter out obvious mismatches such as parts, shells, engines, or non-drivable listings when the user asks "
    "for complete or drivable cars. "
    "Use title and description to judge relevance, and explain why shortlisted listings match or fail the user's criteria. "
    "Do not invent listings. If results are weak, say so and suggest a refined search."
)


def run_agent_turn(client: OpenAI, conversation: list[dict[str, Any]]) -> str:
    _, _, model = resolve_client_config()
    while True:
        completion = client.chat.completions.create(
            model=model,
            messages=conversation,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2,
            top_p=0.7,
            max_tokens=1400,
        )

        message = completion.choices[0].message
        tool_calls = getattr(message, "tool_calls", None) or []

        if tool_calls:
            conversation.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [tool_call.model_dump() for tool_call in tool_calls],
                }
            )

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                raw_arguments = tool_call.function.arguments or "{}"

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

                conversation.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )

            continue

        final_text = message.content or ""
        conversation.append({"role": "assistant", "content": final_text})
        return final_text


def main():
    _, _, model = resolve_client_config()
    client = build_client()
    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]

    print(f"Agent ready with model: {model}")
    print("Type 'exit' or 'quit' to stop.")

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break

        conversation.append({"role": "user", "content": user_input})
        reply = run_agent_turn(client, conversation)
        print(f"\nAgent: {reply}")


if __name__ == "__main__":
    main()
