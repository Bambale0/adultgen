# Rejected frontend removal and rebuild status

Status: the rejected frontend remains removed; a new implementation now exists under `apps/web_app`.

The current React/Vite app is new code based on `docs/WEB_PRODUCT_BRIEF.md`. It does not restore or copy the previous UI.

## What remains removed

- all source from the rejected frontend;
- its obsolete design assumptions and production-readiness claims;
- any unverified email-only session entry point.

## New implementation

- original dark creator shell with responsive navigation;
- public safe-preview feed and private generation workspace;
- server-verified Google Identity Services token exchange;
- server-verified Telegram Login Widget and Telegram Mini App auth;
- recorded adult-policy gate;
- generation, results, billing, wallet, profile, project, avatar, and admin surfaces;
- frontend unit/build gates in CI and a production web container.

## Current launch boundary

The new UI is suitable for staging review. A public paid launch still requires configured OAuth/bot domains, real provider and payment callbacks, adult-category provider approval, production media derivatives, and end-to-end validation.
