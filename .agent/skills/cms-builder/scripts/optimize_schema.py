#!/usr/bin/env python3
"""PocketBase schema + rules optimization (Elementhic).

This script is intentionally idempotent:
- It fetches the current collection schema
- Applies a set of safe, incremental improvements
- Patches the collection only when changes are needed

Run:
  python3 optimize_schema.py --apply
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


REDACTED_WEBHOOK_SECRET = "__WEBHOOK_SECRET__"


def load_env() -> None:
    # Load .env from project root (four levels up from scripts dir)
    env_path = os.path.join(os.path.dirname(__file__), "../../../../.env")
    try:
        with open(env_path, "r") as f:
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
    url = os.environ.get("PUBLIC_POCKETBASE_URL") or os.environ.get("POCKETBASE_URL")
    if not url:
        raise SystemExit("ERROR: PUBLIC_POCKETBASE_URL (or POCKETBASE_URL) must be set")
    email = os.environ.get("POCKETBASE_ADMIN_EMAIL") or os.environ.get("PB_ADMIN_EMAIL")
    password = os.environ.get("POCKETBASE_ADMIN_PASSWORD") or os.environ.get(
        "PB_ADMIN_PASSWORD"
    )
    if not email or not password:
        raise SystemExit(
            "ERROR: Missing POCKETBASE_ADMIN_EMAIL/POCKETBASE_ADMIN_PASSWORD in .env"
        )
    return url.rstrip("/"), email, password


def pb_auth_token(base_url: str, email: str, password: str) -> str:
    auth_url = f"{base_url}/api/collections/_superusers/auth-with-password"
    resp = requests.post(
        auth_url, json={"identity": email, "password": password}, timeout=30
    )
    resp.raise_for_status()
    token = resp.json().get("token")
    if not token:
        raise RuntimeError("PocketBase auth succeeded but token missing")
    return token


def pb_get_collection(base_url: str, token: str, name: str) -> Dict[str, Any]:
    r = requests.get(
        f"{base_url}/api/collections/{name}",
        headers={"Authorization": token},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def pb_patch_collection(
    base_url: str, token: str, name: str, payload: Dict[str, Any]
) -> Dict[str, Any]:
    r = requests.patch(
        f"{base_url}/api/collections/{name}",
        headers={"Authorization": token, "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"PocketBase PATCH {name} failed: {r.status_code} {r.text}")
    return r.json()


def _index_name(sql: str) -> Optional[str]:
    # Example: CREATE UNIQUE INDEX `idx_name` ON `table` (...)
    # NOTE: Do not use a trailing \b after the closing backtick.
    # In SQL, the index name is followed by whitespace, so the boundary check would fail.
    m = re.search(r"\bINDEX\s+`([^`]+)`", sql)
    return m.group(1) if m else None


def _ensure_index(indexes: List[str], desired_sql: str) -> Tuple[List[str], bool]:
    name = _index_name(desired_sql)
    if not name:
        # If we can't parse it, fallback to string presence check.
        if desired_sql in indexes:
            return indexes, False
        return indexes + [desired_sql], True

    changed = False
    out: List[str] = []
    replaced = False
    for idx in indexes:
        if _index_name(idx) == name:
            if idx != desired_sql:
                out.append(desired_sql)
                changed = True
            else:
                out.append(idx)
            replaced = True
        else:
            out.append(idx)

    if not replaced:
        out.append(desired_sql)
        changed = True
    return out, changed


def _field_by_name(fields: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    for f in fields:
        if f.get("name") == name:
            return f
    return None


def _ensure_field(
    fields: List[Dict[str, Any]], field_def: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], bool]:
    name = field_def.get("name")
    if not name:
        return fields, False

    existing = _field_by_name(fields, name)
    if not existing:
        return fields + [field_def], True

    # If exists, keep existing (we avoid unexpected diffs here).
    return fields, False


def _set_field_required(
    fields: List[Dict[str, Any]], name: str, required: bool
) -> Tuple[List[Dict[str, Any]], bool]:
    changed = False
    out: List[Dict[str, Any]] = []
    for f in fields:
        if f.get("name") != name:
            out.append(f)
            continue
        if bool(f.get("required", False)) == required:
            out.append(f)
            continue
        new_f = dict(f)
        new_f["required"] = required
        out.append(new_f)
        changed = True
    return out, changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Optimize PocketBase schema/rules")
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes (default is dry-run)"
    )
    parser.add_argument(
        "--webhook-secret",
        default="",
        help="Webhook secret used in PocketBase rules (or set env WEBHOOK_SECRET)",
    )
    args = parser.parse_args()

    load_env()
    base_url, email, password = get_pb_creds()
    token = pb_auth_token(base_url, email, password)

    webhook_secret = (
        args.webhook_secret
        or os.environ.get("WEBHOOK_SECRET")
        or os.environ.get("PB_WEBHOOK_SECRET")
        or ""
    )
    if not webhook_secret:
        if args.apply:
            raise SystemExit(
                "ERROR: WEBHOOK_SECRET is required for --apply (set env WEBHOOK_SECRET or pass --webhook-secret)"
            )
        webhook_secret = REDACTED_WEBHOOK_SECRET
        print("WARN: WEBHOOK_SECRET missing; using placeholder in dry-run")

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"Mode: {mode}")
    print(f"PocketBase: {base_url}")

    def maybe_patch(name: str, payload: Dict[str, Any]) -> None:
        if not payload:
            return
        print(f"- patch {name}: {', '.join(payload.keys())}")
        if not args.apply:
            return
        pb_patch_collection(base_url, token, name, payload)

    # ------------------------------------------------------------------
    # users: add stripe_customer_id
    users = pb_get_collection(base_url, token, "users")
    users_fields = list(users.get("fields") or [])
    users_fields, users_changed = _ensure_field(
        users_fields,
        {
            "name": "stripe_customer_id",
            "type": "text",
            "required": False,
            "presentable": False,
            "hidden": False,
            "min": 0,
            "max": 0,
            "pattern": "",
            "system": False,
        },
    )
    users_indexes = list(users.get("indexes") or [])
    users_indexes, users_idx_changed = _ensure_index(
        users_indexes,
        "CREATE UNIQUE INDEX `idx_users_stripe_customer_id` ON `users` (`stripe_customer_id`) WHERE `stripe_customer_id` != ''",
    )
    users_payload: Dict[str, Any] = {}
    if users_changed:
        users_payload["fields"] = users_fields
    if users_idx_changed:
        users_payload["indexes"] = users_indexes
    maybe_patch("users", users_payload)

    # ------------------------------------------------------------------
    # user_addresses: add missing address fields used by frontend
    uaddr = pb_get_collection(base_url, token, "user_addresses")
    uaddr_fields = list(uaddr.get("fields") or [])
    field_adds = [
        {
            "name": "line2",
            "type": "text",
            "required": False,
            "presentable": False,
            "hidden": False,
            "min": 0,
            "max": 0,
            "pattern": "",
            "system": False,
        },
        {
            "name": "state",
            "type": "text",
            "required": False,
            "presentable": False,
            "hidden": False,
            "min": 0,
            "max": 0,
            "pattern": "",
            "system": False,
        },
        {
            "name": "phone",
            "type": "text",
            "required": False,
            "presentable": False,
            "hidden": False,
            "min": 0,
            "max": 0,
            "pattern": "",
            "system": False,
        },
    ]
    uaddr_changed = False
    for f in field_adds:
        uaddr_fields, changed = _ensure_field(uaddr_fields, f)
        uaddr_changed = uaddr_changed or changed
    uaddr_payload: Dict[str, Any] = {}
    if uaddr_changed:
        uaddr_payload["fields"] = uaddr_fields
    maybe_patch("user_addresses", uaddr_payload)

    # ------------------------------------------------------------------
    # pages: unique slug
    pages = pb_get_collection(base_url, token, "pages")
    pages_indexes = list(pages.get("indexes") or [])
    pages_indexes, pages_idx_changed = _ensure_index(
        pages_indexes,
        "CREATE UNIQUE INDEX `idx_pages_slug` ON `pages` (`slug`)",
    )
    if pages_idx_changed:
        maybe_patch("pages", {"indexes": pages_indexes})

    # ui_assets: unique key
    ui_assets = pb_get_collection(base_url, token, "ui_assets")
    ui_assets_indexes = list(ui_assets.get("indexes") or [])
    ui_assets_indexes, ui_assets_idx_changed = _ensure_index(
        ui_assets_indexes,
        "CREATE UNIQUE INDEX `idx_ui_assets_key` ON `ui_assets` (`key`)",
    )
    if ui_assets_idx_changed:
        maybe_patch("ui_assets", {"indexes": ui_assets_indexes})

    # collection_images: unique position
    col_imgs = pb_get_collection(base_url, token, "collection_images")
    col_imgs_indexes = list(col_imgs.get("indexes") or [])
    col_imgs_indexes, col_imgs_idx_changed = _ensure_index(
        col_imgs_indexes,
        "CREATE UNIQUE INDEX `idx_collection_images_position` ON `collection_images` (`position`)",
    )
    if col_imgs_idx_changed:
        maybe_patch("collection_images", {"indexes": col_imgs_indexes})

    # ------------------------------------------------------------------
    # user_lists: enforce one row per (user,type)
    user_lists = pb_get_collection(base_url, token, "user_lists")
    user_lists_indexes = list(user_lists.get("indexes") or [])
    # Note: some PB deployments may reject changing an existing index definition.
    # Add a new unique index name instead of mutating the existing one.
    user_lists_indexes, ul_idx_changed = _ensure_index(
        user_lists_indexes,
        "CREATE UNIQUE INDEX `uidx_user_lists_user_type` ON `user_lists` (`user`, `type`)",
    )
    user_lists_payload: Dict[str, Any] = {}
    if ul_idx_changed:
        user_lists_payload["indexes"] = user_lists_indexes
    maybe_patch("user_lists", user_lists_payload)

    # ------------------------------------------------------------------
    # product_variants: index sku (non-unique), enforce unique (product,color,size)
    variants = pb_get_collection(base_url, token, "product_variants")
    variants_fields = list(variants.get("fields") or [])
    variants_fields, color_req_changed = _set_field_required(
        variants_fields, "color", True
    )
    variants_fields, size_req_changed = _set_field_required(
        variants_fields, "size", True
    )

    variants_fields, swatch_added = _ensure_field(
        variants_fields,
        {
            "name": "color_swatch",
            "type": "text",
            "required": False,
            "presentable": False,
            "hidden": False,
            "min": 0,
            "max": 0,
            "pattern": "",
            "system": False,
        },
    )

    variants_fields, v_stock_status_added = _ensure_field(
        variants_fields,
        {
            "name": "stock_status",
            "type": "select",
            "required": False,
            "presentable": False,
            "hidden": False,
            "maxSelect": 1,
            "values": ["in_stock", "low_stock", "out_of_stock"],
            "system": False,
        },
    )
    variants_fields, v_gallery_added = _ensure_field(
        variants_fields,
        {
            "name": "gallery_images",
            "type": "file",
            "required": False,
            "presentable": False,
            "hidden": False,
            "protected": False,
            "maxSelect": 10,
            "maxSize": 5242880,
            "mimeTypes": [
                "image/jpeg",
                "image/png",
                "image/webp",
                "image/gif",
            ],
            "thumbs": ["100x100"],
            "system": False,
        },
    )

    variants_fields, v_main_image_added = _ensure_field(
        variants_fields,
        {
            "name": "main_image",
            "type": "file",
            "required": False,
            "presentable": False,
            "hidden": False,
            "protected": False,
            "maxSelect": 1,
            "maxSize": 5242880,
            "mimeTypes": [
                "image/jpeg",
                "image/png",
                "image/webp",
                "image/gif",
            ],
            "thumbs": ["100x100"],
            "system": False,
        },
    )
    variants_indexes = list(variants.get("indexes") or [])
    variants_indexes, sku_unique_idx_changed = _ensure_index(
        variants_indexes,
        "CREATE UNIQUE INDEX `uidx_product_variants_sku` ON `product_variants` (`sku`) WHERE `sku` != ''",
    )
    variants_indexes, uniq_idx_changed = _ensure_index(
        variants_indexes,
        "CREATE UNIQUE INDEX `idx_product_variants_product_color_size` ON `product_variants` (`product`, `color`, `size`)",
    )
    variants_payload: Dict[str, Any] = {}
    if (
        color_req_changed
        or size_req_changed
        or swatch_added
        or v_stock_status_added
        or v_gallery_added
        or v_main_image_added
    ):
        variants_payload["fields"] = variants_fields
    if sku_unique_idx_changed or uniq_idx_changed:
        variants_payload["indexes"] = variants_indexes
    maybe_patch("product_variants", variants_payload)

    # ------------------------------------------------------------------
    # orders: better ordering + safer unique stripe IDs
    orders = pb_get_collection(base_url, token, "orders")
    orders_indexes = list(orders.get("indexes") or [])
    orders_indexes, o_user_idx = _ensure_index(
        orders_indexes,
        "CREATE INDEX `idx_orders_user` ON `orders` (`user`)",
    )
    orders_indexes, o_user_date_idx = _ensure_index(
        orders_indexes,
        "CREATE INDEX `idx_orders_user_placed_at_override` ON `orders` (`user`, `placed_at_override`)",
    )
    orders_indexes, o_status_idx = _ensure_index(
        orders_indexes,
        "CREATE INDEX `idx_orders_status` ON `orders` (`status`)",
    )
    orders_indexes, o_cs_idx = _ensure_index(
        orders_indexes,
        "CREATE UNIQUE INDEX `idx_orders_stripe_session_id` ON `orders` (`stripe_session_id`) WHERE `stripe_session_id` != ''",
    )
    orders_indexes, o_pi_idx = _ensure_index(
        orders_indexes,
        "CREATE UNIQUE INDEX `idx_orders_stripe_payment_intent` ON `orders` (`stripe_payment_intent`) WHERE `stripe_payment_intent` != ''",
    )
    orders_payload: Dict[str, Any] = {}
    if o_user_idx or o_user_date_idx or o_status_idx or o_cs_idx or o_pi_idx:
        orders_payload["indexes"] = orders_indexes
    maybe_patch("orders", orders_payload)

    # ------------------------------------------------------------------
    # order_items: reporting/perf indexes
    order_items = pb_get_collection(base_url, token, "order_items")
    order_items_indexes = list(order_items.get("indexes") or [])
    order_items_indexes, oi_order = _ensure_index(
        order_items_indexes,
        "CREATE INDEX `idx_order_items_order_id` ON `order_items` (`order_id`)",
    )
    order_items_indexes, oi_prod = _ensure_index(
        order_items_indexes,
        "CREATE INDEX `idx_order_items_product_id` ON `order_items` (`product_id`)",
    )
    order_items_indexes, oi_var = _ensure_index(
        order_items_indexes,
        "CREATE INDEX `idx_order_items_variant_id` ON `order_items` (`variant_id`)",
    )
    order_items_indexes, oi_order_prod = _ensure_index(
        order_items_indexes,
        "CREATE INDEX `idx_order_items_order_product` ON `order_items` (`order_id`, `product_id`)",
    )
    if oi_order or oi_prod or oi_var or oi_order_prod:
        maybe_patch("order_items", {"indexes": order_items_indexes})

    # ------------------------------------------------------------------
    # rules hardening: products writes, webhook secret compatibility
    secret_expr = (
        f'@request.headers.x_webhook_secret = "{webhook_secret}" || '
        f'@request.query.webhook_secret = "{webhook_secret}"'
    )

    products = pb_get_collection(base_url, token, "products")
    prod_payload: Dict[str, Any] = {}
    # Only change write rules; keep list/view public
    if (products.get("createRule") or "") != secret_expr:
        prod_payload["createRule"] = secret_expr
    if (products.get("updateRule") or "") != secret_expr:
        prod_payload["updateRule"] = secret_expr
    if prod_payload:
        maybe_patch("products", prod_payload)

    # orders/order_items: accept header secret OR query secret
    for name in ["orders", "order_items"]:
        col = pb_get_collection(base_url, token, name)
        payload: Dict[str, Any] = {}
        for rule in ["createRule", "updateRule", "deleteRule"]:
            cur = col.get(rule)
            if cur and cur != secret_expr:
                payload[rule] = secret_expr
        if payload:
            maybe_patch(name, payload)

    # user_lists: remove secret from listRule; allow secret on update/delete for compatibility
    user_lists = pb_get_collection(base_url, token, "user_lists")
    ul_payload: Dict[str, Any] = {}
    if (user_lists.get("listRule") or "") != "@request.auth.id = user.id":
        ul_payload["listRule"] = "@request.auth.id = user.id"
    if (user_lists.get("viewRule") or "") != "@request.auth.id = user.id":
        ul_payload["viewRule"] = "@request.auth.id = user.id"
    # keep createRule as strict user ownership
    create_rule = '@request.auth.id != "" && @request.auth.id = user.id'
    if (user_lists.get("createRule") or "") != create_rule:
        ul_payload["createRule"] = create_rule
    # update/delete: allow user OR secret
    user_or_secret = f"@request.auth.id = user.id || {secret_expr}"
    if (user_lists.get("updateRule") or "") != user_or_secret:
        ul_payload["updateRule"] = user_or_secret
    if (user_lists.get("deleteRule") or "") != user_or_secret:
        ul_payload["deleteRule"] = user_or_secret
    if ul_payload:
        maybe_patch("user_lists", ul_payload)

    print("Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
