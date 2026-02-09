#!/usr/bin/env python3
"""Migrate product_variants.variant_image -> product_variants.main_image.

PocketBase file fields require a new file upload; you can't re-point a file field
to an existing filename. This script:

1) Lists product_variants records with variant_image set
2) Downloads the existing variant_image file bytes
3) Uploads the same bytes into main_image via multipart PATCH

Run:
  python3 migrate_variant_image_to_main_image.py           # dry-run
  python3 migrate_variant_image_to_main_image.py --apply   # migrate

Notes:
- By default, it does NOT delete/clear variant_image.
- It skips records where main_image is already set.
"""

import argparse
import io
import mimetypes
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import requests
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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


def fetch_variants(base_url: str, token: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    page = 1
    while True:
        r = requests.get(
            f"{base_url}/api/collections/product_variants/records",
            headers={"Authorization": token},
            params={"page": page, "perPage": 200, "filter": 'variant_image != ""'},
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


def guess_content_type(
    filename: str, fallback: str = "application/octet-stream"
) -> str:
    ct, _ = mimetypes.guess_type(filename)
    return ct or fallback


def download_file(
    base_url: str, token: str, collection_id: str, record_id: str, filename: str
) -> Tuple[bytes, str]:
    url = f"{base_url}/api/files/{collection_id}/{record_id}/{filename}"
    r = requests.get(
        url,
        headers={"Authorization": token},
        verify=False,
        timeout=60,
    )
    r.raise_for_status()
    content_type = r.headers.get("content-type") or guess_content_type(filename)
    return r.content, content_type


def upload_main_image(
    base_url: str,
    token: str,
    variant_id: str,
    filename: str,
    content: bytes,
    content_type: str,
) -> Dict[str, Any]:
    files = {
        "main_image": (
            filename,
            io.BytesIO(content),
            content_type,
        )
    }
    r = requests.patch(
        f"{base_url}/api/collections/product_variants/records/{variant_id}",
        headers={"Authorization": token},
        files=files,
        verify=False,
        timeout=120,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Upload failed: {r.status_code} {r.text}")
    data = r.json()
    if not isinstance(data, dict):
        raise RuntimeError("Upload succeeded but response is not JSON object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate product_variants.variant_image -> main_image"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes (default is dry-run)"
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Process at most N records (0 = all)"
    )
    args = parser.parse_args()

    load_env()
    base_url, email, password = get_pb_creds()
    token = pb_auth_token(base_url, email, password)

    variants = fetch_variants(base_url, token)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"Mode: {mode}")
    print(f"PocketBase: {base_url}")
    print(f"Variants with variant_image: {len(variants)}")

    processed = 0
    migrated = 0
    skipped = 0
    failed = 0

    for v in variants:
        if args.limit and processed >= args.limit:
            break

        processed += 1
        vid = str(v.get("id") or "").strip()
        cid = str(v.get("collectionId") or "").strip()
        variant_image = str(v.get("variant_image") or "").strip()
        main_image = str(v.get("main_image") or "").strip()
        sku = str(v.get("sku") or "").strip()

        label = sku or vid
        if not vid or not cid or not variant_image:
            print(f"- {label}: SKIP (missing ids/filename)")
            skipped += 1
            continue
        if main_image:
            print(f"- {label}: SKIP (main_image already set)")
            skipped += 1
            continue

        print(f"- {label}: migrate {variant_image} -> main_image")
        if not args.apply:
            continue

        try:
            content, content_type = download_file(
                base_url, token, cid, vid, variant_image
            )
            resp = upload_main_image(
                base_url, token, vid, variant_image, content, content_type
            )
            new_main = str(resp.get("main_image") or "").strip()
            if not new_main:
                raise RuntimeError("Upload returned empty main_image")
            migrated += 1
        except Exception as e:
            failed += 1
            print(f"  ERROR: {e}")

    print("\nDone")
    print(f"Processed: {processed}")
    print(f"Migrated: {migrated}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
