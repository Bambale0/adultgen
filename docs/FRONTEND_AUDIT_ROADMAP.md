# Frontend rebuild roadmap

The rejected frontend remains deleted. This roadmap tracks the new implementation described by `WEB_PRODUCT_BRIEF.md`.

## Epic FE-01 — Product direction and safety boundary

- Approved flow map and wireframes.
- Leonardo/CreatePorn/Stellar references translated into original AdultGen tokens.
- Auth and 18+ gate separated into verifiable steps.

## Epic FE-02 — App shell and routing hardening

- `useWebRoute` URL synchronization with `history.pushState`.
- Browser `popstate` support.
- `AppShell`/`Sidebar`/`TopBar` extraction.
- Responsive drawer and product status areas.

## Epic FE-03 — Feature modules

- Move feature UI into `features/*` modules as screens grow.
- Move shared UI primitives into `components/*`.
- Preserve dynamic model capability rules and API ownership boundaries.

## Epic FE-04 — End-to-end readiness

- Component tests and production build in CI.
- Auth, adult consent, generation, result, billing, profile, and admin flows.
- Visible staging review before any paid launch claim.
