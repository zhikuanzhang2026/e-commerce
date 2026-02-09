<!--
SYNC IMPACT REPORT
Version: 1.5.2 -> 1.5.3
List of modified principles:
- V. Backend & Architecture (Adaptive Edge): Clarified documentation secret hygiene and workflow reference policy.
Added sections:
None
Removed sections:
None
Templates requiring updates:
- .specify/templates/plan-template.md (✅ verified)
- .specify/templates/spec-template.md (✅ verified)
- .specify/templates/tasks-template.md (✅ verified)
Command files requiring updates:
- .opencode/command/*.md (✅ verified)
Runtime docs requiring updates:
- .agent/docs/atomic-api-guide.md (✅ updated)
Automation/scripts requiring updates:
None
Follow-up TODOs:
None
-->

# ELEMENTHIC Project Constitution

## Core Principles

### I. SvelteKit + Svelte 5 Protocol (The Runes)
- **Reactivity (MUST)**: Use `$state`, `$derived`, and `$props` for reactivity.
- **Props (SHOULD)**: Destructure `$props()` when it improves readability.
- **State Management (MUST)**:
    - **Server-synced**: Use **TanStack Query v6** for all server-synced state (cart, wishlist, products).
    - **Local UI**: Use Svelte 5 **Runes** for transient UI state.
    - **Shared Logic Location**: Shared state logic MUST live in `src/lib/stores/*.svelte.ts`.
- **Data Fetching (MUST)**: Primary page data MUST be fetched via SSR in `+page.server.ts`.
- **API Routes (MUST)**: SvelteKit API routes MUST wrap handlers with `apiHandler`.
- **UI Composition (SHOULD)**: Prefer `{#snippet}` for local UI composition and reuse.
- **Rationale**: Consistent reactivity/state boundaries reduce bugs and keep SSR predictable.

### II. Apple UX Style & Aesthetics
- **Design Standard (MUST)**: Customer-facing UI MUST not ship with unstyled browser defaults.
- **Styling Engine (MUST)**: **Tailwind CSS v4** is mandatory. Define design tokens via `@theme`.
- **Typography (SHOULD)**: Use the project font tokens (e.g., Manrope, Optima) with clear hierarchy.
- **Icons (MUST)**: Use **Lucide Svelte** (stroke width 1.5px-2px) with consistent sizing.
- **Color System (MUST)**: Use curated HSL tokens and gradients; avoid ad-hoc component colors.
- **Motion (MUST)**: Animations MUST use GPU-safe properties (`transform`, `opacity`). Prefer
  Svelte `transition:` and `animate:flip` for UI motion.
- **Rationale**: Premium consistency is part of the product; inconsistency creates compounding UX debt.

### III. Performance & Assets
- **Preloading (MUST)**: Internal navigation links MUST set `data-sveltekit-preload-data="hover"`
  by default. Document any exceptions in code.
- **Image Optimization (MUST)**: Use `@sveltejs/enhanced-img` with `decoding="async"` and
  `loading="lazy"` unless above-the-fold content requires eager loading.
- **Layout Stability (MUST)**: Images MUST set explicit `width`/`height` or `aspect-ratio` to prevent CLS.
- **Rationale**: These defaults protect LCP/CLS with minimal ongoing effort.

### IV. Type Safety (Type Convergence)
- **Source of Truth (MUST)**: Extend from `src/lib/pocketbase-types.ts` (generated from DB).
- **Domain Types (MUST)**: Define view models and DTOs in `src/lib/types.ts` by extending DB types.
- **Validation (MUST)**: Use **Zod v4** (imported as `zod`) for all schemas.
  `sveltekit-superforms` MUST use the `zod4` adapter. `zod/v3` legacy imports are forbidden.
    - *Exception*: For `zodClient` adapters requiring `superRefine`, `as any` casting is allowed
      only when strict types conflict with library internals.
- **Protocol (MUST)**:
    - **PocketBase**: Responses MUST use types from `src/lib/pocketbase-types.ts`. Never use
      `RecordModel` or `any`. Handle expansions with explicit interfaces.
    - **API Handlers**: Use `catch (e: unknown)` and extract errors safely. Never return untyped JSON.
    - **DTOs**: Define explicit Data Transfer Objects in `src/lib/types.ts`.
- **Rationale**: One type chain prevents drift and keeps runtime validation aligned with compile-time types.

### V. Backend & Architecture (Adaptive Edge)
- **Three-Tier Architecture (MUST)**:
    - **Tier 1 (Display)**: Optimized queries for `products`, `pages`.
    - **Tier 2 (Ops)**: Precise tracking of `variants`, `SKUs`, and financial details.
    - **Tier 3 (Extension)**: JSON attributes for non-searchable metadata.
- **Stripe Hybrid Driver (MUST)**: Stripe is the source of truth for prices; SvelteKit webhooks sync
  data to PocketBase (marketing source of truth).
- **Optimistic Concurrency Control (OCC) (MUST)**: Perform server-side stock verification before
  updates to prevent overselling.
- **Security (MUST)**: Enforce strict `$env` separation for server-side secrets. Use `withAdmin` for
  privileged operations.
- **Automation Policy (MUST)**: Core business logic (orders, inventory) stays in SvelteKit; n8n
  handles side effects (email notifications, reporting).
- **Side-Effect Idempotency (MUST)**: Webhook handlers (Stripe, etc.) MUST be idempotent and MUST
  log execution status to PocketBase before triggering n8n flows.
- **Webhook Authenticity (MUST)**: Inbound webhook endpoints MUST verify the sender.
  Preferred: provider signature verification. Acceptable: a shared secret in an HTTP header validated
  server-side.
- **Secret Transport (SHOULD)**: Shared secrets SHOULD be passed via headers, not query parameters.
- **Workflow Secrets (MUST)**: Secrets MUST NOT be hard-coded in code, docs, or tracked workflow
  exports. Use `$env` (server) or n8n credentials/environment variables.
- **Documentation Secret Hygiene (MUST)**: Documentation examples MUST use placeholder secret values
  (for example `<WEBHOOK_SECRET>`), never real keys or tokens.
- **Workflow Reference Policy (SHOULD)**: Runtime docs SHOULD refer to n8n workflow names/IDs in the
  instance rather than assuming local tracked JSON export filenames.
- **Workflow Export Hygiene (MUST)**: Workflow JSON committed to the repo MUST be sanitized (no
  `pinData`, sample payloads with PII, API keys, or webhook secrets). If not sanitized, keep it
  untracked.
- **Core Modules Strategy (MUST)**:
    - **Cart**: Managed via `cart.svelte.ts` (TanStack Query). Supports `addRawItem` for wishlist integration.
    - **Orders**: Strict state machine (`pending` -> `paid` -> `processing`) in `src/lib/server/orders.ts`.
    - **Payment**: Stripe Elements integration with strictly typed PaymentIntent handling.
- **Rationale**: Authenticated, idempotent side effects keep orders correct and protect customer data.

### VI. Error Handling & Debugging
- **Compiler/Linter First (MUST)**: Fix new compiler warnings and lint warnings as part of the change.
- **Automated Validation (MUST)**: `npm run lint` and `npm run check` MUST pass before code is
  committed or merged.
- **Context Awareness (MUST)**: Maintain clear boundaries between SSR and CSR execution contexts.
- **Rationale**: Fast feedback loops prevent shipping runtime-only failures.

### VII. Code Elegance & Efficiency (The "Essential Luxury" Code)
- **Conciseness (SHOULD)**: Prefer the smallest solution that stays readable and expressive.
- **Platform First (SHOULD)**: Prefer built-in platform features (Svelte runes, fetch, etc.) over
  third-party bloat.
- **Maintainability (SHOULD)**: Prefer declarative patterns over imperative ones; every line must
  earn its place.
- **Rationale**: Lower complexity increases velocity and reduces regression risk.

### VIII. Spec-Driven Workflow (The Law)
- **Traceability (MUST)**: Every code change MUST trace back to an approved task in
  `specs/<feature>/tasks.md`.
- **Chain of Custody (MUST)**: Features progress strictly through: `Constitution` ->
  `specs/<feature>/spec.md` -> `specs/<feature>/plan.md` -> `specs/<feature>/tasks.md` -> `Code`.
- **Plan Fidelity (MUST)**: Deviations from `plan.md` during implementation require a documented
  amendment to the plan; silent drift is a violation.
- **Rationale**: Spec-driven constraints prevent scope creep and keep implementation deterministic.

## Governance
- **Authority**: This constitution supersedes all other coding practices in the repository.
- **Amendments**:
    - Any change MUST be made via PR and MUST include an updated Sync Impact Report.
    - Ratification date MUST remain the original adoption date.
    - Last amended date MUST be updated to the amendment date.
- **Versioning**:
    - MAJOR: Backward-incompatible governance changes, removals, or redefinitions of principles.
    - MINOR: New principle/section added or materially expanded guidance.
    - PATCH: Clarifications, wording, typo fixes, and non-semantic refinements.
- **Compliance Reviews**:
    - Plans MUST include a "Constitution Check" gate before design and MUST re-check after design.
    - PRs MUST show traceability (links to `specs/<feature>/spec.md`, `specs/<feature>/plan.md`,
      `specs/<feature>/tasks.md`, plus task IDs).
    - PRs MUST NOT include secrets or workflow exports containing secrets/PII/pinData.
    - Reviewers MUST reject PRs violating MUST-level rules, regardless of functional correctness.

**Version**: 1.5.3 | **Ratified**: 2026-01-27 | **Last Amended**: 2026-02-09
