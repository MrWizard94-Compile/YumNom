"""Spike 4: measure Grok's ability to generate a valid, constraint-honoring weekly plan.

Streams one plan for a fixed test profile and reports:
  - time to first content (spec gate: < 5 s)
  - total generation time (target: < 30 s)
  - token usage and estimated cost
  - JSON validity + constraint adherence (budget, allergy blocklist, cook time)

Required environment variables:
  XAI_API_KEY   from https://console.x.ai
Optional:
  XAI_MODEL     default "grok-4-1-fast" (check https://docs.x.ai for current model ids)
"""

import json
import os
import sys
import time

import requests

API_URL = "https://api.x.ai/v1/chat/completions"
PROMPT_VERSION = "v1"

PROFILE = {
    "household": "2 adults, 2 kids (ages 6 and 9)",
    "weekly_budget_usd": 150,
    "allergies": ["peanut"],
    "max_dinner_minutes": 35,
    "dislikes": ["mushrooms"],
}

# Deterministic allergy enforcement (SPEC §12) — the guarantee lives here, not in the prompt.
ALLERGY_BLOCKLIST = {"peanut": ["peanut", "peanuts", "peanut butter", "groundnut", "satay"]}

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "days": {
            "type": "array",
            "minItems": 7,
            "maxItems": 7,
            "items": {
                "type": "object",
                "properties": {
                    "day": {"type": "string"},
                    "dinner": {"type": "string"},
                    "minutes": {"type": "integer"},
                    "est_cost_usd": {"type": "number"},
                    "ingredients": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "item": {"type": "string"},
                                "quantity": {"type": "string"},
                            },
                            "required": ["item", "quantity"],
                        },
                    },
                },
                "required": ["day", "dinner", "minutes", "est_cost_usd", "ingredients"],
            },
        },
        "week_total_usd": {"type": "number"},
    },
    "required": ["days", "week_total_usd"],
}


def request_plan(api_key, model):
    body = {
        "model": model,
        "stream": True,
        "stream_options": {"include_usage": True},
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "weekly_plan", "schema": PLAN_SCHEMA},
        },
        "messages": [
            {
                "role": "system",
                "content": (
                    f"[prompt {PROMPT_VERSION}] You plan practical weekly dinners for busy families "
                    "shopping at Walmart. Use common, inexpensive supermarket ingredients. "
                    "Respect the budget, allergy, time, and dislike constraints exactly."
                ),
            },
            {"role": "user", "content": f"Create a 7-day dinner plan for: {json.dumps(PROFILE)}"},
        ],
    }
    started = time.perf_counter()
    first_content_at = None
    content_parts = []
    usage = {}
    with requests.post(
        API_URL,
        json=body,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=120,
        stream=True,
    ) as response:
        response.raise_for_status()
        for raw_line in response.iter_lines():
            if not raw_line or not raw_line.startswith(b"data: "):
                continue
            payload = raw_line[len(b"data: "):]
            if payload == b"[DONE]":
                break
            chunk = json.loads(payload)
            usage = chunk.get("usage") or usage
            choices = chunk.get("choices") or []
            delta = choices[0].get("delta", {}).get("content") if choices else None
            if delta:
                if first_content_at is None:
                    first_content_at = time.perf_counter()
                content_parts.append(delta)
    finished = time.perf_counter()
    return (
        "".join(content_parts),
        (first_content_at or finished) - started,
        finished - started,
        usage,
    )


def check_constraints(plan):
    failures = []
    days = plan.get("days", [])
    if len(days) != 7:
        failures.append(f"expected 7 days, got {len(days)}")
    total = sum(day.get("est_cost_usd", 0) for day in days)
    if total > PROFILE["weekly_budget_usd"]:
        failures.append(f"budget exceeded: ${total:.2f} > ${PROFILE['weekly_budget_usd']}")
    for day in days:
        if day.get("minutes", 0) > PROFILE["max_dinner_minutes"]:
            failures.append(f"{day.get('day')}: {day.get('minutes')} min over limit")
        for ingredient in day.get("ingredients", []):
            text = ingredient.get("item", "").lower()
            for allergen in PROFILE["allergies"]:
                if any(term in text for term in ALLERGY_BLOCKLIST[allergen]):
                    failures.append(f"ALLERGY VIOLATION: '{ingredient['item']}' on {day.get('day')}")
    return failures, total


def main():
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        sys.exit("Missing XAI_API_KEY (get one at https://console.x.ai).")
    model = os.environ.get("XAI_MODEL", "grok-4-1-fast")

    print(f"Model: {model}  (prompt {PROMPT_VERSION})")
    content, first_content_s, total_s, usage = request_plan(api_key, model)

    print(f"Time to first content: {first_content_s:.1f}s  (gate: < 5s)")
    print(f"Total generation time: {total_s:.1f}s  (target: < 30s)")
    if usage:
        tokens_in, tokens_out = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
        cost = tokens_in / 1e6 * 0.20 + tokens_out / 1e6 * 0.50  # grok-4-1-fast list prices
        print(f"Tokens: {tokens_in} in / {tokens_out} out  (~${cost:.4f}/plan)")

    try:
        plan = json.loads(content)
    except json.JSONDecodeError as error:
        sys.exit(f"RESULT: FAIL — output is not valid JSON: {error}")

    failures, total = check_constraints(plan)
    print(f"Plan total: ${total:.2f} vs budget ${PROFILE['weekly_budget_usd']}")
    for day in plan.get("days", []):
        print(f"  {day['day']:<10} {day['dinner'][:50]:<52} {day['minutes']:>3} min  ${day['est_cost_usd']:.2f}")

    if failures:
        print("\nConstraint failures:")
        for failure in failures:
            print(f"  - {failure}")
    passed = not failures and first_content_s < 5 and total_s < 30
    print(f"\nRESULT: {'PASS' if passed else 'FAIL — tune prompt/model and re-run'}")


if __name__ == "__main__":
    main()
