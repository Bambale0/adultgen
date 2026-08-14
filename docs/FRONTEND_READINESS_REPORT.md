# AdultGen frontend readiness report

The new React/Vite web app is ready for controlled staging/demo iteration after green CI and visual review. It is not ready for full public paid production launch.

Implemented surfaces include the public safe-preview feed, generation composer, results, projects, private avatars/assets, wallet and billing, profile, Google/Telegram authentication, recorded 18+ consent, and a protected admin workspace.

Production promotion remains blocked on real-domain OAuth configuration, Telegram BotFather domain binding, approved provider/payment credentials, callback delivery, production-grade derivatives, and an end-to-end backup/restore drill. See `docs/PRODUCTION_DEPLOYMENT.md` and `docs/FRONTEND_AUDIT_ROADMAP.md`.
