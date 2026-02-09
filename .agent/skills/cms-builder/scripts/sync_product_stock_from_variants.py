#!/usr/bin/env python3
"""Sync products stock fields from product_variants.

PocketBase doesn't provide DB triggers, so aggregated fields like:
- products.stock_quantity
- products.stock_status

can drift when variants are edited directly in the Admin UI.

This script recomputes aggregated stock from product_variants and updates products.

Run:
  python3 sync_product_stock_from_variants.py        # dry-run
  python3 sync_product_stock_from_variants.py --apply
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

import requests
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


LOW_STOCK_THRESHOLD = 5


def load_env() -> None:
    # Load .env from project root (four levels up from scripts dir)
    env_path = os.path.join(os.path.dirname(__file__), "../../../../.env")
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())
    except FileNotFoundError:
        print(f"WARN: .env not found at {env_path}")


def get_creds() -> Dict[str, str]:
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
        raise SystemExit("ERROR: PUBLIC_POCKETBASE_URL (or POCKETBASE_URL) must be set")
    if not email or not password:
        raise SystemExit(
            "ERROR: Missing POCKETBASE_ADMIN_EMAIL/POCKETBASE_ADMIN_PASSWORD (or PB_ADMIN_*) in .env"
        )
    return {"base_url": base_url, "email": email, "password": password}


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
        raise RuntimeError("PocketBase auth succeeded but token missing")
    return token


def fetch_all_records(
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
        total_pages = int(data.get("totalPages") or 1)
        if page >= total_pages:
            break
        page += 1
    return items


def compute_stock_status(total_stock: int) -> str:
    if total_stock <= 0:
        return "out_of_stock"
    if total_stock <= LOW_STOCK_THRESHOLD:
        return "low_stock"
    return "in_stock"


def as_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync product_variants.stock_status from stock_quantity"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply updates (default is dry-run)"
    )
    args = parser.parse_args()

    load_env()
    creds = get_creds()
    base_url = creds["base_url"]
    token = auth_token(base_url, creds["email"], creds["password"])

    products = fetch_all_records(base_url, token, "products")
    variants = fetch_all_records(base_url, token, "product_variants")

    variants_by_product: Dict[str, List[Dict[str, Any]]] = {}
    for v in variants:
        pid = v.get("product")
        if isinstance(pid, str) and pid:
            variants_by_product.setdefault(pid, []).append(v)

    variant_updates: List[Dict[str, Any]] = []
    for v in variants:
        vid = v.get("id")
        if not isinstance(vid, str) or not vid:
            continue

        stock_qty = as_int(v.get("stock_quantity")) or 0
        desired_status = compute_stock_status(stock_qty)
        current_status = v.get("stock_status")

        if current_status == desired_status:
            continue

        variant_updates.append(
            {
                "id": vid,
                "product": v.get("product"),
                "sku": v.get("sku"),
                "stock_quantity": stock_qty,
                "current_status": current_status,
                "new_status": desired_status,
            }
        )

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"Mode: {mode}")
    print(f"PocketBase: {base_url}")
    print(f"Products scanned: {len(products)}")
    print(f"Variants scanned: {len(variants)}")
    print(f"Variants needing update: {len(variant_updates)}")

    for u in variant_updates:
        print(
            "-",
            u.get("sku") or u["id"],
            f"stock={u['stock_quantity']}",
            f"status {u['current_status']} -> {u['new_status']}",
        )

        if not args.apply:
            continue

        payload: Dict[str, Any] = {
            "stock_status": u["new_status"],
        }
        r = requests.patch(
            f"{base_url}/api/collections/product_variants/records/{u['id']}",
            headers={"Authorization": token, "Content-Type": "application/json"},
            json=payload,
            verify=False,
            timeout=60,
        )
        if r.status_code != 200:
            print(f"  ERROR: update failed: {r.status_code} {r.text}")
        else:
            print("  OK")

    products_without_variants = [
        p
        for p in products
        if isinstance(p.get("id"), str) and p.get("id") not in variants_by_product
    ]
    if products_without_variants:
        print(f"Products without variants: {len(products_without_variants)}")
        for p in products_without_variants:
            print("-", p.get("slug") or p.get("id"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
