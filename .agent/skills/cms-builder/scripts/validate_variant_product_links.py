#!/usr/bin/env python3
"""Validate product_variants -> products linkage health.

Checks:
1) Each product_variants record has a valid `product` relation.
2) Linked product exists.
3) Linked product has non-empty `stripe_price_id`.

Run:
  python3 validate_variant_product_links.py
"""

import os
import sys
from typing import Any, Dict, List, Tuple

import requests
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_env() -> None:
    env_path = os.path.join(os.path.dirname(__file__), "../../../../.env")
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
    except FileNotFoundError:
        print(f"WARN: .env not found at {env_path}")


def get_creds() -> Tuple[str, str, str]:
    base_url = (
        os.environ.get("PUBLIC_POCKETBASE_URL")
        or os.environ.get("POCKETBASE_URL")
        or ""
    ).rstrip("/")
    email = (
        os.environ.get("POCKETBASE_ADMIN_EMAIL")
        or os.environ.get("PB_ADMIN_EMAIL")
        or ""
    )
    password = (
        os.environ.get("POCKETBASE_ADMIN_PASSWORD")
        or os.environ.get("PB_ADMIN_PASSWORD")
        or ""
    )
    if not base_url:
        raise SystemExit("ERROR: Missing PUBLIC_POCKETBASE_URL/POCKETBASE_URL")
    if not email or not password:
        raise SystemExit(
            "ERROR: Missing POCKETBASE_ADMIN_EMAIL/POCKETBASE_ADMIN_PASSWORD"
        )
    return base_url, email, password


def auth_token(base_url: str, email: str, password: str) -> str:
    r = requests.post(
        f"{base_url}/api/collections/_superusers/auth-with-password",
        json={"identity": email, "password": password},
        verify=False,
        timeout=30,
    )
    r.raise_for_status()
    token = r.json().get("token")
    if not token:
        raise RuntimeError("Auth succeeded but token missing")
    return token


def fetch_all(
    base_url: str, token: str, collection: str, per_page: int = 200
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    page = 1
    while True:
        r = requests.get(
            f"{base_url}/api/collections/{collection}/records",
            headers={"Authorization": token},
            params={"page": page, "perPage": per_page},
            verify=False,
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        batch = data.get("items") or []
        if isinstance(batch, list):
            items.extend([x for x in batch if isinstance(x, dict)])
        if page >= int(data.get("totalPages") or 1):
            break
        page += 1
    return items


def main() -> int:
    load_env()
    base_url, email, password = get_creds()
    token = auth_token(base_url, email, password)

    products = fetch_all(base_url, token, "products")
    variants = fetch_all(base_url, token, "product_variants")

    product_by_id = {str(p.get("id")): p for p in products if p.get("id")}

    missing_product_ref: List[Dict[str, Any]] = []
    broken_product_ref: List[Dict[str, Any]] = []
    missing_stripe_price: List[Dict[str, Any]] = []

    for v in variants:
        variant_id = str(v.get("id") or "")
        sku = str(v.get("sku") or "")
        product_id = str(v.get("product") or "").strip()

        if not product_id:
            missing_product_ref.append({"variantId": variant_id, "sku": sku})
            continue

        p = product_by_id.get(product_id)
        if not p:
            broken_product_ref.append(
                {"variantId": variant_id, "sku": sku, "productId": product_id}
            )
            continue

        stripe_price_id = str(p.get("stripe_price_id") or "").strip()
        if not stripe_price_id:
            missing_stripe_price.append(
                {
                    "variantId": variant_id,
                    "sku": sku,
                    "productId": product_id,
                    "productSlug": str(p.get("slug") or ""),
                }
            )

    print("PocketBase:", base_url)
    print("products_total:", len(products))
    print("variants_total:", len(variants))
    print("missing_product_ref:", len(missing_product_ref))
    print("broken_product_ref:", len(broken_product_ref))
    print("missing_product_stripe_price_id:", len(missing_stripe_price))

    if missing_product_ref:
        print("\n[missing_product_ref]")
        for row in missing_product_ref[:20]:
            print("-", row)

    if broken_product_ref:
        print("\n[broken_product_ref]")
        for row in broken_product_ref[:20]:
            print("-", row)

    if missing_stripe_price:
        print("\n[missing_product_stripe_price_id]")
        for row in missing_stripe_price[:30]:
            print("-", row)

    return 0


if __name__ == "__main__":
    sys.exit(main())
