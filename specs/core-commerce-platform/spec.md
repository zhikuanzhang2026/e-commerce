# Feature Specification: Core E-Commerce Platform

**Feature Branch**: `000-baseline-platform`  
**Created**: 2026-01-27  
**Status**: Baseline (Reverse-Engineered, Updated 2026-02-24)
**Input**: Existing codebase analysis

## User Scenarios & Testing

### User Story 1 - Product Discovery & Browsing (Priority: P1)
As a shopper, I can browse products in a grid, filter them by category/attributes, and search for specific items so that I can find what I want to buy.

**Why this priority**: Core value proposition of the e-commerce site.
**Independent Test**: Can be tested by navigating to `/shop`, applying a filter (e.g., "HOODIES"), and verifying only hooded items appear.

**Acceptance Scenarios**:
1. **Given** browsing the shop, **When** clicking a category (e.g., "Mens"), **Then** the product list updates via URL params.
2. **Given** the search bar, **When** typing "Fear of God", **Then** the list filters in real-time.
3. **Given** 6+ products, **When** clicking "View More Products", **Then** the next batch of 6 products is appended.

---

### User Story 2 - Account Management & Auth (Priority: P2)
As a returning customer, I can log in, view my order history, and manage my profile.

**Why this priority**: Essential for customer retention and order tracking.
**Independent Test**: Can be tested by navigating to `/account` and verifying auth states.

**Acceptance Scenarios**:
1. **Given** an unauthenticated state, **When** visiting `/account`, **Then** redireted to login.
2. **Given** a logged-in state, **When** visiting `/account`, **Then** profile details are fetched from PocketBase.

---

### User Story 3 - Wishlist (Priority: P3)
As a shopper, I can save items to a wishlist for later consideration.

**Why this priority**: High-value feature for engagement.
**Independent Test**: Can be tested by clicking the "heart" icon on a `ProductCard` and verifying it appears in `/wishlist`.

---

## Requirements

### Functional Requirements
- **FR-001**: System MUST fetch product data from PocketBase via SSR in `+page.server.ts`.
- **FR-002**: System MUST support multi-facet filtering (Pillar, Type, Size, Color) via the Drawer component.
- **FR-003**: System MUST support sorting by Price (Low/High) and Newness.
- **FR-004**: System MUST utilize `$derived` runes for real-time filtering logic based on URL store and state.
- **FR-005**: System MUST use `@sveltejs/enhanced-img` for all product thumbnails.
- **FR-006**: System MUST use product-level pricing as the single source of truth (`products.stripe_price_id` / Stripe price lookup); variant-level price override is not supported.
- **FR-007**: System MUST derive variant stock status from `product_variants.stock_quantity` at runtime; `stock_status` is not persisted.

### Key Entities
- **Product**: ID, Title, Description, Slug, Category, `stripe_product_id`, `stripe_price_id`, `main_image`, `attributes`, and computed display price.
- **ProductVariant**: `sku`, `color`, `color_swatch`, `size`, `stock_quantity`, `gallery_images` (stock status is computed runtime).
- **Category**: Title, Slug, Parent Relationship.
- **User**: Email, Name, Auth tokens (managed by PocketBase).

## Success Criteria

### Measurable Outcomes
- **SC-001**: Hero images load with `decoding="async"` and `loading="lazy"` to maintain high LCP scores.
- **SC-002**: Filter operations complete in < 100ms on the client.
- **SC-003**: Page navigation preloads on hover via `data-sveltekit-preload-data="hover"`.
