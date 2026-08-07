# Historical frontend removal

Status: the rejected historical frontend remains intentionally removed.

The old `apps/web_app` implementation was deleted because it was not acceptable as a product UI. It must not be restored or used as the visual base for future work.

A new, independent frontend line now starts at:

- `apps/orbital_web`
- `docs/FRONTEND_PRODUCT_BRIEF_V2.md`

The new Orbital Web package was designed from a newly approved reference direction and only reuses backend API contracts, not the removed UI implementation.

## Historical removal included

- old React/Vite app under `apps/web_app`;
- old frontend Docker/static Nginx setup;
- old admin web panel;
- old frontend audit/readiness docs.

## Rule going forward

Do not recover `apps/web_app` from Git history or copy its component/layout code. Extend Orbital Web through focused PRs, keep CI/typecheck/build green, and require visual staging review before claiming production readiness.
