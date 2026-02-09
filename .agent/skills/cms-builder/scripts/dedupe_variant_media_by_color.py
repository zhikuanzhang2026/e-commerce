#!/usr/bin/env python3
"""Deduplicate variant media by (product,color).

Problem:
- `product_variants` are SKU-level records (color/size).
- In practice, images are identical across sizes for the same color.
- PocketBase file fields are stored per-record, so uploading the same image for
  each size creates many duplicate copies.

Solution (Scheme 1):
- Keep media on ONE "master" variant per (product,color)
- Clear `main_image` and `gallery_images` on the other size variants
- Frontend falls back to the color master media

Safety:
- By default, this script verifies that all `main_image` files in a group are
  byte-identical before clearing.
- Use --no-verify-hash to skip hashing.

Run:
  python3 dedupe_variant_media_by_color.py               # dry-run
  python3 dedupe_variant_media_by_color.py --apply       # apply changes
"""

import argparse
import hashlib
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

import requests
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


SIZE_ORDER = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "O/S", "ONE SIZE"]


def size_rank(size_label: str) -> Tuple[int, int, str]:
    # Rank known sizes first; then numeric sizes; then lexicographic.
    norm = str(size_label or "").strip().upper()
    if norm in SIZE_ORDER:
        return (0, SIZE_ORDER.index(norm), norm)
    try:
        n = int(norm)
        return (1, n, norm)
    except Exception:
        return (2, 0, norm)


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


def get_pb_creds() -> Tuple[str, str, str]:
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
    return base_url, email, password


def pb_auth_token(base_url: str, email: str, password: str) -> str:
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


def sha256_of_url(url: str, token: str) -> str:
    r = requests.get(url, headers={"Authorization": token}, verify=False, timeout=60)
    r.raise_for_status()
    return hashlib.sha256(r.content).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deduplicate variant media by (product,color)"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes (default is dry-run)"
    )
    parser.add_argument(
        "--no-verify-hash",
        action="store_true",
        help="Skip hashing verification (faster, less safe)",
    )
    args = parser.parse_args()

    load_env()
    base_url, email, password = get_pb_creds()
    token = pb_auth_token(base_url, email, password)

    variants = fetch_all_records(base_url, token, "product_variants")
    mode = "APPLY" if args.apply else "DRY-RUN"
    verify = not args.no_verify_hash
    print(f"Mode: {mode}")
    print(f"Verify hash: {verify}")
    print(f"PocketBase: {base_url}")
    print(f"Variants scanned: {len(variants)}")

    # Group by (product,color)
    groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for v in variants:
        pid = str(v.get("product") or "").strip()
        color = str(v.get("color") or "").strip()
        if not pid or not color:
            continue
        groups.setdefault((pid, color), []).append(v)

    changed_groups = 0
    cleared_records = 0
    skipped_groups = 0

    for (pid, color), vs in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        media_vs = []
        for v in vs:
            main_image = str(v.get("main_image") or "").strip()
            gallery = v.get("gallery_images")
            gallery_len = len(gallery) if isinstance(gallery, list) else 0
            if main_image or gallery_len > 0:
                media_vs.append(v)

        if len(media_vs) <= 1:
            continue

        # Choose master: smallest size rank, then sku for stability
        def key(v: Dict[str, Any]) -> Tuple[Tuple[int, int, str], str]:
            return (size_rank(v.get("size") or ""), str(v.get("sku") or ""))

        master = sorted(media_vs, key=key)[0]
        master_id = str(master.get("id") or "")
        master_sku = str(master.get("sku") or "")

        # Verify main_image hashes are identical across the group
        if verify:
            hashes = set()
            for v in media_vs:
                vid = str(v.get("id") or "").strip()
                cid = str(v.get("collectionId") or "").strip()
                fn = str(v.get("main_image") or "").strip()
                if not (vid and cid and fn):
                    continue
                url = f"{base_url}/api/files/{cid}/{vid}/{fn}"
                hashes.add(sha256_of_url(url, token))
                if len(hashes) > 1:
                    break
            if len(hashes) > 1:
                skipped_groups += 1
                print(
                    f"- SKIP {pid} {color}: multiple different main_image contents; keep as-is"
                )
                continue

        print(
            f"- {pid} {color}: keep media on {master_sku or master_id}, clear {len(media_vs) - 1} records"
        )

        if not args.apply:
            changed_groups += 1
            cleared_records += len(media_vs) - 1
            continue

        # Clear media fields on non-master variants
        for v in media_vs:
            vid = str(v.get("id") or "").strip()
            if not vid or vid == master_id:
                continue

            payload: Dict[str, Any] = {
                "main_image": "",
                "gallery_images": [],
            }
            r = requests.patch(
                f"{base_url}/api/collections/product_variants/records/{vid}",
                headers={"Authorization": token, "Content-Type": "application/json"},
                json=payload,
                verify=False,
                timeout=60,
            )
            if r.status_code != 200:
                raise RuntimeError(
                    f"Failed to clear media for {vid}: {r.status_code} {r.text}"
                )
            cleared_records += 1
        changed_groups += 1

    print("\nDone")
    print(f"Groups total: {len(groups)}")
    print(f"Groups changed: {changed_groups}")
    print(f"Groups skipped: {skipped_groups}")
    print(f"Records cleared: {cleared_records}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
