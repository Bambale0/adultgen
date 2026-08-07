# AdultGen Orbital Web — Product Brief V2

Status: implementation brief for the new frontend. This is a fresh UI package and does not reuse the removed `apps/web_app` implementation.

## Approved visual reference

The approved direction is the user-supplied `stitch_stellar_content_feed` reference pack:

- Orbital Feed Neon Purple Edition
- Deploy Content Neon Purple
- Profile Operator 01 Neon Purple
- Mission Detail / Telemetry Log
- Neo Aether / Orbital Command design tokens

The implementation uses the reference as a design language, not as copied application code.

## Product flow map

```text
Public safe feed
  -> web-session handshake
  -> 18+ policy gate
  -> live feed
  -> Deploy Studio
      -> workspace (avatar/project/scene)
      -> generation reservation
      -> provider task
      -> telemetry/results
  -> Operator profile
  -> Credit Core / checkout
```

## Route wireframes

### `/` — Orbital Feed

- Fixed 280px tactical sidebar on desktop, 64px sector bar on mobile.
- Safe preview feed before 18+ consent.
- Live backend feed only after a session + adult consent.
- Masonry signal cards with save/report/remix affordances.
- Search and Deploy entry remain always visible.

### `/studio` — Deploy Content

- Prompt and negative constraints.
- Six backend-supported generation modes.
- Reference upload + URL references.
- Aspect ratio, resolution, duration, audio controls.
- Credit reserve estimate is explanatory only; backend wallet ledger remains source of truth.
- Workspace is created through existing Core API before first launch.

### `/missions` — Telemetry

- Generation queue and lifecycle statuses.
- Provider task identifier, reservation, charge, errors, result assets.
- Manual refresh backed by `/generations` endpoints.

### `/profile` — Operator

- Profile identity and visibility.
- Editable bio.
- Published signal gallery.

### `/billing` — Credit Core

- Wallet projection.
- Credit package selection.
- CrocoPay order and checkout flow through existing backend endpoints.

### `/admin` — separate future surface

Admin remains an independent privileged surface. It should use the same Orbital design tokens but a separate auth/session contract based on `ADMIN_API_TOKEN` or future admin identity. It is intentionally not mixed into the public/user bundle in this foundation PR.

## Component system decision

- React 19.2 + TypeScript.
- Vite 8.1 build.
- No component framework; visual primitives are local CSS/React to preserve the supplied direction and avoid fighting a generic design system.
- Shared primitives in the first foundation: tactical panel, panel header, status tag, KPI cell, terminal field, deploy button, task rows.
- Core API base remains `/api` by default.

## Design tokens

- Carbon: `#131313`
- Low surface: `#1c1b1b`
- Panel: `#201f1f`
- Magenta: `#ff45a2` / `#c50275`
- Cyan: `#00f2ff`
- Acid green: `#a0f11c`
- Command type: Archivo Narrow
- Data type: JetBrains Mono
- Interface type: Space Grotesk
- 280px desktop sidebar, 24px content gutters, 12px card radius, 2px control radius.
- Global scanline layer plus controlled neon atmospheric glow.

## Safety / privacy contract

- No explicit backend feed is fetched for anonymous users in the new UI.
- Protected studio/profile/telemetry routes require session and 18+ consent.
- Billing requires session but not adult feed access.
- Policy checks and wallet accounting are never duplicated or bypassed client-side.
- Reference assets go to the existing private reference upload endpoint.

## E2E test plan

1. Anonymous `/` renders safe signals and no explicit live media request.
2. Web session handshake persists token locally.
3. 18+ acceptance unlocks live feed and protected routes.
4. Studio creates workspace then generation task with expected backend payload.
5. Telemetry refresh displays callback results/errors.
6. Profile edit and visibility toggle persist through API.
7. Billing package -> order -> CrocoPay redirect.
8. Browser back/forward follows route history.
9. Mobile navigation remains usable at 320px width.
10. Gateway serves SPA routes while `/api/*` continues proxying to FastAPI.

## Readiness statement

This PR is a new frontend foundation suitable for review/staging. It must not be called production-ready until CI is green and staging validates provider callbacks, payments, media delivery, moderation, and backup/restore.
