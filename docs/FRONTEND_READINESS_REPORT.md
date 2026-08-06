# Frontend Readiness Report

Дата: 2026-08-06

## Executive summary

Frontend AdultGen уже прошёл важную инженерную фазу: web-first shell отделён от admin entry, добавлены frontend quality gates, URL/history routing вынесен в `useWebRoute`, а shell-компоненты `AppShell`, `Sidebar`, `TopBar` выделены как typed contracts.

Проект можно считать готовым к следующему этапу controlled staging demo, но нельзя честно называть полностью production-ready для платного public launch без закрытия блокеров ниже.

## Confirmed ready

### Quality gates

- `npm run typecheck` добавлен и проходит в CI.
- `npm run lint` добавлен как safe frontend gate.
- `npm run build` запускает typecheck перед Vite build.
- GitHub Actions отдельно проверяет backend и frontend.
- Frontend build gate уже проходил на PR #39, #40, #41, #42.

### App entry separation

- `/admin*` рендерит standalone `AdminPanel`.
- User app не смешан с admin token flow.
- Admin token хранится отдельно от user web session.
- Admin UI имеет отдельный CSS контур.

### Routing foundation

- `useWebRoute` читает стартовый route из `window.location.pathname`.
- `history.pushState` используется для route navigation.
- `popstate` поддерживает browser back/forward.
- `RoutedUserApp` связывает старый `App.tsx` с новым route hook через safe bridge.

### Shell component contracts

- Добавлены `AppShell`, `Sidebar`, `TopBar`.
- Shell контракты используют route metadata, а не магические строки.
- `TopBar` поддерживает status/error rendering через `aria-live="polite"`.
- Компоненты уже проходят TypeScript graph и smoke tests через `ShellContractHarness`.

### Product surface currently available in frontend

- Landing.
- Age gate.
- Studio.
- Generation history/result cards.
- External media import action.
- Publication action.
- Feed/Profile/Collection views.
- Billing packages/order/checkout UI.
- Wallet balance visibility.
- Admin workspace: users, generations, publications, payments, wallet adjustment, audit.

## Not production-ready yet

### FE blocker 1 — legacy `App.tsx` is still too large

`App.tsx` remains a god component. Shell contracts are extracted, but inline sidebar/topbar JSX has not yet been fully replaced inside `App.tsx`.

Required before production polish:

- Replace inline sidebar with `Sidebar`.
- Replace inline topbar with `TopBar`.
- Move main route content into dedicated feature modules.
- Remove bridge-only `ShellContractHarness` once the replacement is complete.

### FE blocker 2 — feature modules are not isolated yet

Studio, Billing, Feed, Profile, Collection, and landing UI still live inside the large `App.tsx` file.

Required next:

- `features/studio/*`.
- `features/billing/*`.
- `features/feed/*`.
- `features/profile/*`.
- `features/auth/*`.
- `features/landing/*`.

### FE blocker 3 — no frontend unit/component test runner yet

Current frontend protection is typecheck/lint/build plus backend smoke tests that inspect source contracts. This is acceptable for early MVP, but not enough for production-grade frontend confidence.

Required next:

- Add Vitest.
- Add React Testing Library.
- Add component tests for navigation, billing, studio launch, media result cards, and admin dangerous actions.

### FE blocker 4 — no E2E browser flow yet

Core user journeys are not covered by Playwright/Cypress.

Required before paid public launch:

- Web auth → age gate → studio.
- Launch generation → see callback result.
- Import external result → publish.
- Billing package → checkout redirect.
- Admin hide publication → audit event visible.

### FE blocker 5 — safety UX needs more explicit user-facing language

Backend moderation exists, but frontend should make safety outcomes clearer.

Required:

- Blocked prompt explanation.
- Human review state.
- Report publication modal.
- Moderation outcome state on own publications.

## Cross-functional blockers outside frontend

These are not frontend-only but affect readiness:

- Real blur/thumbnail processing must replace placeholder derivative copies.
- Public media delivery needs stricter age-gated access rules before launch.
- Real auth must replace deterministic MVP web session identity.
- Adult-category payment/provider approval must be confirmed in writing.
- Production secrets, domain, TLS, backups, and restore drill must be completed.
- Provider callback and payment webhook should be tested end-to-end on staging.

## Readiness matrix

| Area | Status | Notes |
| --- | --- | --- |
| Frontend CI gates | Ready | typecheck/lint/build are enforced. |
| Admin entry separation | Ready | `/admin*` is isolated from user app. |
| URL routing foundation | Ready | `useWebRoute`, pushState, popstate are present. |
| Shell contracts | Ready | `AppShell`, `Sidebar`, `TopBar` are extracted. |
| Shell replacement in App | Partial | Contracts exist; inline JSX still needs replacement. |
| Feature modularization | Partial | Still mostly inside `App.tsx`. |
| Billing UI | MVP-ready | Packages/order/checkout flow exists. |
| Wallet UI | MVP-ready | Balance projection is visible. |
| Admin UI | MVP-ready | Workspace exists; more filters/search can be added. |
| Frontend component tests | Not ready | Need Vitest/RTL. |
| Browser E2E tests | Not ready | Need Playwright/Cypress. |
| Production launch readiness | Not ready | Several cross-functional blockers remain. |

## Recommended next PR order

1. Replace inline `sidebar/topbar` in `App.tsx` with extracted shell components.
2. Extract `StudioCard` and generation result components into `features/studio`.
3. Extract `BillingCard` and wallet card into `features/billing`.
4. Extract feed/profile/collection cards.
5. Add Vitest + React Testing Library.
6. Add Playwright staging smoke.
7. Add frontend error boundary and empty/loading states.
8. Add safety UX states for moderation outcomes.

## Final verdict

Frontend is ready for controlled staging/demo iteration.

Frontend is not yet ready for full public paid production launch.

The main reason is not missing screens anymore. The main reason is hardening: `App.tsx` decomposition, component tests, E2E flows, safety UX, real media derivative processing, and production provider validation.
