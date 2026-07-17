"""Spike 3: measure how well recipe ingredients resolve to purchasable Walmart SKUs.

Runs the 10 recipes in recipes.json through the walmart.io affiliate Search API
and reports the match rate against the spec's >=90% release gate.

Required environment variables (or entries in a .env file at the repo root; from spike 1 onboarding):
  WALMART_CONSUMER_ID       walmart.io consumer ID
  WALMART_PRIVATE_KEY_PATH  path to the RSA private key PEM uploaded to walmart.io
  WALMART_KEY_VERSION       key version (default: "1")
Optional:
  WALMART_ZIP               ZIP code for availability context
"""

import base64
import json
import os
import sys
import time
from pathlib import Path

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

SEARCH_URL = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/search"
MATCH_RATE_GATE = 0.90
CANDIDATES_PER_INGREDIENT = 5


def load_env_file():
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


def load_credentials():
    load_env_file()
    consumer_id = os.environ.get("WALMART_CONSUMER_ID")
    key_path = os.environ.get("WALMART_PRIVATE_KEY_PATH")
    if not consumer_id or not key_path:
        sys.exit(
            "Missing credentials. Set WALMART_CONSUMER_ID and WALMART_PRIVATE_KEY_PATH "
            "(and optionally WALMART_KEY_VERSION, WALMART_ZIP). See spikes/1-walmart-affiliate-application.md."
        )
    private_key = serialization.load_pem_private_key(
        Path(key_path).read_bytes(), password=None
    )
    return consumer_id, private_key, os.environ.get("WALMART_KEY_VERSION", "1")


def signed_headers(consumer_id, private_key, key_version):
    timestamp = str(int(time.time() * 1000))
    payload = f"{consumer_id}\n{timestamp}\n{key_version}\n".encode()
    signature = private_key.sign(payload, padding.PKCS1v15(), hashes.SHA256())
    return {
        "WM_CONSUMER.ID": consumer_id,
        "WM_CONSUMER.INTIMESTAMP": timestamp,
        "WM_SEC.KEY_VERSION": key_version,
        "WM_SEC.AUTH_SIGNATURE": base64.b64encode(signature).decode(),
    }


def search_ingredient(ingredient, consumer_id, private_key, key_version):
    params = {"query": ingredient, "numItems": CANDIDATES_PER_INGREDIENT}
    zip_code = os.environ.get("WALMART_ZIP")
    if zip_code:
        params["zipCode"] = zip_code
    response = requests.get(
        SEARCH_URL,
        params=params,
        headers=signed_headers(consumer_id, private_key, key_version),
        timeout=15,
    )
    response.raise_for_status()
    return response.json().get("items", [])


def best_candidate(items):
    """A match = an in-stock, online-purchasable item; prefer cheapest such candidate."""
    purchasable = [
        item
        for item in items
        if item.get("availableOnline") and item.get("stock", "Available") == "Available"
    ]
    if not purchasable:
        return None
    return min(purchasable, key=lambda item: item.get("salePrice") or float("inf"))


def main():
    consumer_id, private_key, key_version = load_credentials()
    recipes = json.loads((Path(__file__).parent / "recipes.json").read_text())["recipes"]

    ingredients = sorted({ing for recipe in recipes for ing in recipe["ingredients"]})
    print(f"{len(recipes)} recipes, {len(ingredients)} unique ingredients\n")

    matches = {}
    for ingredient in ingredients:
        try:
            candidate = best_candidate(
                search_ingredient(ingredient, consumer_id, private_key, key_version)
            )
        except requests.RequestException as error:
            print(f"  ERROR  {ingredient}: {error}")
            candidate = None
        matches[ingredient] = candidate
        status = (
            f"${candidate.get('salePrice', '?'):<7} {candidate.get('name', '')[:60]}"
            if candidate
            else "-- NO PURCHASABLE MATCH --"
        )
        print(f"  {'OK ' if candidate else 'MISS'}  {ingredient:<28} {status}")
        time.sleep(0.25)  # stay polite against the 5k/day budget

    matched = sum(1 for candidate in matches.values() if candidate)
    rate = matched / len(ingredients)
    print(f"\nMatch rate: {matched}/{len(ingredients)} = {rate:.0%} (gate: >={MATCH_RATE_GATE:.0%})")
    print("RESULT: PASS" if rate >= MATCH_RATE_GATE else "RESULT: FAIL — revise SPEC §6 matching strategy")

    per_recipe = [
        (recipe["name"], sum(1 for ing in recipe["ingredients"] if matches.get(ing)), len(recipe["ingredients"]))
        for recipe in recipes
    ]
    print("\nPer recipe:")
    for name, hit, total in per_recipe:
        print(f"  {hit}/{total}  {name}")


if __name__ == "__main__":
    main()
