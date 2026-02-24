# Implementation Plan: Core E-Commerce Platform

**Branch**: `000-baseline-platform` | **Date**: 2026-01-27 | **Spec**: [./spec.md]
**Input**: Feature specification from `/specs/core-commerce-platform/spec.md`

## Summary
The current implementation is a modern, high-performance e-commerce platform built with SvelteKit 2 and PocketBase. It leverages Svelte 5 Runes for highly efficient reactivity and Tailwind CSS v4 for styling. The architecture follows a strict SSR-first approach with Apple-inspired design principles.

## Technical Context

**Language/Version**: TypeScript 5.9, Svelte 5.45+
**Primary Dependencies**: SvelteKit 2, Tailwind CSS 4, PocketBase SDK, Stripe, TanStack Query v6, Superforms, Valibot, Zod
**Storage**: PocketBase (Remote DB), Decoupled Edge Architecture
**Testing**: Vitest (Unit/Integration), Playwright (E2E)
**Target Platform**: Edge Platforms (via adapter-auto)
**Project Type**: Web Application (SvelteKit)
**Performance Goals**: Optimized LCP via enhanced-img, hover preloading, and asynchronous decoding.
**Constraints**: Absolute separation of server-only secrets; HSL-based design system.

## Commerce Data Model Constraints (Updated 2026-02-24)

- Product price source is unified at `products` level via Stripe mapping (`stripe_price_id`).
- Variant-level price override is removed (`product_variants.price_override` no longer exists).
- Variant stock state is computed from `stock_quantity` at runtime (`stock_status` is not persisted).
- Variant media field remains enabled (`gallery_images`) for color-level image reuse.

## Constitution Check

| Principle | Check | Status |
|-----------|-------|--------|
| Svelte 5 Runes | `$state`, `$derived`, `$props` used | ✅ |
| Mandatory SSR | `+page.server.ts` handles primary data | ✅ |
| Apple UX | High-vibe design, premium motion | ✅ |
| Asset Opt. | `@sveltejs/enhanced-img` in use | ✅ |
| Security | `$env` used for PocketBase/Stripe secrets | ✅ |

## Project Structure

### Documentation
```text
specs/core-commerce-platform/
├── plan.md              # This file
└── spec.md              # Baseline Requirements
```

## Automation & External Integrations

### n8n Workflows (Active)
1.  **[Notify] Order Confirmation**:
    - **Trigger**: SvelteKit API (`/api/webhooks/resend`)
    - **Logic**: Renders HTML template -> Sends via Resend.
    - **Webhook**: `https://n8n.elementhic.com/webhook/order-created-v1`
2.  **[Sync] Product Logic**:
    - **Status**: Migrated to SvelteKit Internal Webhooks.

### Payment & Tax
- **Provider**: Stripe (Automatic Tax enabled).
- **Compliance**: Checkout UI displays estimated tax; backend persists `amount_tax`.

### Source Code
```text
src/
├── lib/
│   ├── components/      # UI Components (ProductCard, Drawer, etc.)
│   ├── pb/              # PocketBase client & types
│   └── stores/          # Shared state (rarely used due to runes)
├── routes/              # SvelteKit Routing hierarchy
│   ├── account/
│   ├── shop/
│   ├── checkout/
│   └── wishlist/
└── app.html             # HTML entry template (preloading enabled)

static/                  # Public assets
tests/                   # Vitest & Playwright test suites
```

**Structure Decision**: Standard SvelteKit monorepo structure utilizing `$lib` for shared components and services. Routing is used as the primary feature boundary.

## Complexity Tracking
*No current violations of the constitution detected.*
