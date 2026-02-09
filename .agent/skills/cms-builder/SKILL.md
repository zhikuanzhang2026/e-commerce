---
name: cms-builder
description: Guide for configuring, managing, and operating the Elementhic CMS (PocketBase) via AI Agents.
---

# Elementhic CMS Manager Skill

This skill provides a complete toolset for managing the Elementhic E-commerce backend. It follows a **Three-Tier Data Architecture** designed for high performance, data integrity, and AI automation.

## 1. Architecture Overview (Three-Tier Model)

### Tier 1: Core Display (Fast Checkouts)
 Optimized for frontend read performance and cached rendering.
- **`products`**: Contains generic info and high-frequency filter fields (`slug`, `title`, `price`, `material`, `gender`).
- **`orders`**: Stores **Immutable JSON Snapshots** of purchase history. Frontend reads ONLY from `orders.items` array.
- **`ui_sections`**: Page content blocks with direct media attachments or references.

### Tier 2: Analytics & Operations (Precision)
 Used for backend logic, inventory management, and financial reporting.
- **`order_items`**: Atomic line items derived from orders. Used for sales reports, returns, and refunds.
- **`product_variants`**: SKU-level tracking for inventory (`stock_quantity`) and specific pricing (`price_override`).
  `color` is the display label; `color_swatch` is the swatch color value; `main_image`/`gallery_images` are variant media.

**Media rule**: For the same `product` + `color`, images SHOULD be stored once and reused across sizes.
- **`user_addresses`**: Customer address book with labels.

### Tier 3: Flexible Extension (Agility)
 JSON-based storage for non-critical or evolving attributes.
- **`products.attributes`**: Stores specs like `{ "care": "...", "fit": "oversized" }`.
- **`user_lists`**: Consolidated Cart and Wishlist items (distinguished by `type`).

---

## 2. Core Collections Schema

### `products`
The central catalog entity.
- `title`, `slug`, `price` (Legacy display string), `is_featured` (bool)
- Variants are inferred from reverse relation `product_variants(product)`.
- `attributes` (json): Structured specs (Material, Care, Fit).
- **Relations**: `category`, `product_variants(product)` (Reverse relation).

### `orders`
The transaction record.
- `items` (json): **SNAPSHOT**. Contains full copy of product data at time of purchase. **DO NOT EDIT** after creation.
- `status`: `pending`, `paid`, `shipped`, `cancelled`.
- `amount_tax`: Automatic tax calculation result from Stripe Tax.
- `shipping_address` (json): Snapshot of destination.

### `user_lists`
Unified list management.
- `type`: `cart` | `wishlist` | `save_for_later`
- `items` (json): Array of `{ productId, variantId, quantity }`. **Note**: Prices are NOT stored here; fetched real-time.

---

## 3. Operational Tools (Schema Admin)

### `manage.py` (Schema Admin)
Low-level schema migration tool.
- `apply`: Pushes local `schema_definitions.json` to remote DB.
- `dump`: Pulls remote DB schema to local JSON.

---

4. **Hybrid Driver Sync (Stripe ↔ PB)**
   - **Trigger**: Creating/Updating/Deleting products in Stripe Dashboard.
   - **Auto-Mirroring**: `product.created` in Stripe automatically creates a stub in PB and links IDs.
   - **Sync Rule**: Stripe governs `active` status. PB governs rich descriptions/galleries.
   - **Metadata**: Stripe product `metadata.pb_product_id` is the single source of truth for linking.

---

## 5. Operational Rules (CRITICAL)

1. **Snapshot Rule**: precise historical data is stored in `orders.items`. Never rely on `products` table for historical order details as product prices/titles change over time.
2. **Stock Logic**: Always deduct stock from `product_variants`. If `variant_id` is missing, the product MUST have exactly one variant.
3. **Workflow Rule**: Create products in **Stripe first** for automatic mirroring, then enhance/decorate in **PocketBase**.
4. **Media**: Use `ui_sections.image` for one-off headers. Use `media_library` (conceptual) or shared URL references for reusable assets.

---

## 6. Atomic Operations API (Concurrency Safe)

为防止并发场景下的超卖和重复扣减，库存和优惠券更新通过 SvelteKit 原子 API 处理：

### 库存扣减 - `POST /api/inventory/deduct`
- **用途**: 批量原子扣减库存
- **特性**: 检查库存充足后才扣减，自动更新 `product_variants.stock_status`
- **认证**: `X-Webhook-Secret` 请求头

### 优惠券递增 - `POST /api/coupons/increment`
- **用途**: 原子递增优惠券使用次数
- **特性**: 检查有效性、过期时间、使用上限
- **认证**: `X-Webhook-Secret` 请求头

---

## 7. n8n Workflow Integration

订单处理由 n8n 工作流编排（工作流名：`Elementhic Stripe Order`）。

### 流程
```
Stripe Webhook → 验证签名 → 创建订单 → 原子库存扣减 → 原子优惠券递增 → 发送邮件 → 删除购物车
```

### 状态追踪 (order.notes)
```json
{
  "schema": "v2",
  "steps": { "stock": true, "coupon": true, "email": true },
  "ts": { "created": "...", "stock": "...", "coupon": "...", "email": "..." }
}
```

### 幂等性
- 已完成的步骤会被跳过
- Stripe 重发 webhook 时自动补跑未完成步骤
