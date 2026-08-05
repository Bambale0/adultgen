# AdultGen Frontend Audit and Implementation Roadmap

## Scope

This document is the frontend team's audit of the current AdultGen web application and admin panel. It covers the website app, admin workspace, API clients, styling, build pipeline, accessibility, operational UX, and the implementation order for the next frontend epics.

Current app shape:

- `apps/web_app/src/App.tsx` is the user-facing web app shell.
- `apps/web_app/src/AdminPanel.tsx` is the standalone `/admin` workspace.
- `apps/web_app/src/api.ts` is the user API client.
- `apps/web_app/src/adminApi.ts` is the admin API client.
- `apps/web_app/src/styles.css` and `apps/web_app/src/admin.css` are global CSS files.
- `apps/web_app/src/main.tsx` switches between user app and admin app.
- CI currently runs backend checks and a frontend build.

## Executive assessment

The frontend is functional for an MVP, but it is not yet organized like a mature production frontend. The biggest risks are not visual polish; the biggest risks are maintainability, state coupling, missing route-level separation, incomplete frontend quality gates, and weak UX around long-running generation/payment/import flows.

The product already has strong backend primitives: auth, 18+ gate, generation lifecycle, media import/publish, billing, wallet, moderation, admin API, and production deployment. The frontend now needs to catch up and become a reliable product shell on top of those contracts.

## Findings

### 1. Application architecture

`App.tsx` currently owns route state, session state, wallet state, studio state, billing state, profile state, feed state, publication state, generation state, and most UI components. This creates a god component. It is acceptable for fast prototyping, but it will slow every future change.

Risks:

- High merge conflict probability.
- Hard to test feature slices.
- Hard to reason about loading/error state per route.
- Higher risk of accidental cross-feature regressions.

Target:

- Keep `App.tsx` as shell only.
- Move feature UI into `features/*` modules.
- Move shared UI primitives into `components/*`.
- Move hooks/state helpers into `hooks/*`.

### 2. Routing

Current routing is lightweight and internal-state based. The app derives initial route from `window.location.pathname`, but navigation mostly changes React state and does not consistently update browser history.

Risks:

- Refresh/deep-link behavior is incomplete.
- Back/forward browser buttons are not reliable product navigation.
- Admin and user route separation exists at entrypoint level, but user routes need stronger route boundaries.

Target:

- Introduce a small router adapter without heavy dependency first.
- Update URL on route change.
- Listen to `popstate`.
- Keep route metadata in `routes.ts`.

### 3. API client layer

`api.ts` is useful but too broad. It mixes transport, types, and all user feature calls. `adminApi.ts` is cleaner because it is feature-specific.

Risks:

- Types and endpoints become hard to review.
- No single place for request telemetry, request id, timeout, or auth failure behavior.
- Error messages are generic and inconsistent.

Target:

- Extract `coreClient.ts` transport helper.
- Split user API into feature clients over time: `authApi`, `studioApi`, `mediaApi`, `billingApi`, `walletApi`, `feedApi`, `profileApi`.
- Keep a backwards-compatible barrel export during migration.

### 4. Async UX

There is already a basic stale-response cleanup pattern in `useEffect`. That is good. The next issue is action-level state: many buttons can be double-clicked while an action is running, and the UI often only has a global `statusMessage`.

Risks:

- Duplicate orders/generation/import attempts.
- Confusing status messages when two actions run close together.
- Weak loading and empty states.

Target:

- Add shared action-state helper.
- Disable active action buttons.
- Add per-section loading/empty/error states.
- Add refresh affordances to every data section.

### 5. Generation and media UX

The generation lifecycle exists, but the UI still behaves like a technical demo. It should guide the user through the funnel: prompt, safety reminders, cost estimate, create task, see status, import, publish.

Risks:

- User does not understand why an external provider result must be imported.
- Publication can feel like a backend concept instead of a product action.
- Feed/profile outcome is not prominent enough.

Target:

- Add a generation lifecycle timeline.
- Make external/stored result state obvious.
- Separate primary CTA from secondary technical controls.
- Add contextual help for import and publish.

### 6. Billing UX

Billing flow works, but needs production-grade confidence: package selection, order creation, redirect, post-payment balance update, and status explanation.

Risks:

- User returns from checkout and does not know whether payment succeeded.
- Wallet refresh is manual.
- Payment order status is too raw.

Target:

- Add payment status explainer.
- Add post-checkout return screen handling.
- Add wallet auto-refresh after checkout start/return.
- Keep provider status visible for support.

### 7. Admin UX

Admin panel is correctly separated from user app. Good foundation. It now needs operational ergonomics: filters, search, clearer risk indicators, and safer irreversible actions.

Risks:

- Large tables become noisy.
- Dangerous actions rely on free text reason only.
- Token in localStorage is acceptable for MVP internal tooling, but it is not final auth.

Target:

- Add filters/search per table.
- Add confirm affordance for delete/hide/block/wallet adjustment.
- Add recent-audit side panel.
- Long-term: replace static token with admin identity/session.

### 8. Accessibility and responsive behavior

The UI uses semantic elements in places, but it needs a dedicated pass.

Risks:

- Missing visible focus states.
- Status/error text may not be announced to assistive tech.
- Dense tables on mobile may become unusable.

Target:

- Add `aria-live` to status/error regions.
- Add focus-visible styling.
- Ensure buttons have clear labels.
- Add mobile table/card fallback for admin.

### 9. Styling system

Current CSS is fast and effective, but still global. There are repeated concepts: cards, pills, tables, button rows, status states.

Risks:

- CSS regressions across user/admin app.
- Hard to update design consistently.

Target:

- Introduce shared CSS tokens and primitives.
- Keep admin CSS isolated.
- Gradually move feature-specific styles next to feature modules or prefix strongly.

### 10. Frontend quality gates

CI builds the frontend, which catches TypeScript errors because `npm run build` runs `tsc`. There is no separate frontend lint, unit tests, or bundle/report guard yet.

Risks:

- Build catches type errors late but does not enforce style/accessibility patterns.
- No automated tests for route behavior or key feature rendering.

Target:

- Add `npm run typecheck`.
- Add `npm run lint` as a no-op-safe first step or ESLint later.
- Add Vitest/Testing Library when dependencies are acceptable.
- Add smoke tests for route shell contracts at repository level immediately.

## Implementation order

### Epic FE-01 — Frontend audit and quality gates

Deliverables:

- This audit document.
- Frontend quality scripts in `package.json`.
- CI split for `typecheck` and `build`.
- Smoke tests for audit/roadmap and package scripts.

Acceptance criteria:

- CI validates backend tests and frontend build/typecheck.
- The roadmap is committed and becomes the source of truth for frontend sequencing.

### Epic FE-02 — App shell and routing hardening

Deliverables:

- `useWebRoute` hook.
- URL synchronization with `history.pushState`.
- `popstate` support.
- `AppShell`/`Sidebar`/`TopBar` extraction.

Acceptance criteria:

- Route changes update URL.
- Browser back/forward works.
- Existing pages still render.

### Epic FE-03 — Shared UI primitives

Deliverables:

- `components/Button.tsx` or primitive class contract.
- `components/StatusBanner.tsx`.
- `components/CodeBlock.tsx`.
- `components/MetricCard.tsx`.
- `components/EmptyState.tsx`.

Acceptance criteria:

- Repeated UI pieces are removed from `App.tsx`.
- Status/error region supports `aria-live`.

### Epic FE-04 — API transport split

Deliverables:

- `api/coreClient.ts` transport helper.
- Feature API modules.
- Backwards-compatible barrel exports.
- Unified error extraction.

Acceptance criteria:

- Existing imports still work.
- Feature APIs are easier to review.

### Epic FE-05 — Studio UX upgrade

Deliverables:

- Studio feature module.
- Generation lifecycle timeline.
- Import/publish state explainer.
- Safer disabled states while actions run.

Acceptance criteria:

- User can understand task lifecycle without reading backend terminology.
- Duplicate action risk is reduced.

### Epic FE-06 — Billing UX upgrade

Deliverables:

- Billing feature module.
- Checkout status explainer.
- Wallet refresh states.
- Return-from-payment handling.

Acceptance criteria:

- Payment flow has clear next steps after redirect.
- Wallet balance is surfaced consistently.

### Epic FE-07 — Feed/profile/collection UX upgrade

Deliverables:

- Better publication cards.
- Report action in feed.
- Save/remix affordances.
- Empty/loading states.

Acceptance criteria:

- User can browse, save, report, and understand blur/safety state.

### Epic FE-08 — Admin panel ergonomics

Deliverables:

- Table filters/search.
- Confirm dangerous actions.
- Better audit side panel.
- Safer wallet adjustment UX.

Acceptance criteria:

- Admin can operate without scanning raw tables manually.
- Dangerous actions require explicit reason and confirmation.

### Epic FE-09 — Accessibility/responsive pass

Deliverables:

- Focus-visible styling.
- `aria-live` status/error regions.
- Better mobile admin tables.
- Keyboard navigation checks.

Acceptance criteria:

- Core flows are usable by keyboard.
- Status/error messages are announced.

### Epic FE-10 — Frontend test layer

Deliverables:

- Vitest + Testing Library setup.
- Route shell tests.
- Billing/studio/admin smoke rendering tests.

Acceptance criteria:

- CI runs frontend unit tests.
- Core UI contracts are covered.

## Current priority

Start with FE-01, then FE-02, then FE-03. Do not start visual polish before app shell, routing, and state boundaries are fixed.
