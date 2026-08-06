# AdultGen Documentation — English

This directory is the English documentation entrypoint.

AdultGen currently has no production frontend. The previous Mini App and web implementations were removed; the decision and replacement entry criteria are documented in [`../FRONTEND_RESET.md`](../FRONTEND_RESET.md).

The canonical English architecture documents currently live in the root `docs/` directory:

- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — platform architecture, runtime applications, bot mirrors, generation, billing, feed, and admin boundaries.
- [`../MODEL_CAPABILITIES.md`](../MODEL_CAPABILITIES.md) — Kie/Seedream/Seedance model capabilities, payload modes, mutual exclusions, reference mapping, and validation rules.
- [`../DATA_MODEL.md`](../DATA_MODEL.md) — PostgreSQL schema draft for users, wallets, payments, projects, scenes, media, publications, partner payouts, broadcasts, and audit.
- [`../API_CONTRACTS.md`](../API_CONTRACTS.md) — REST API contract draft for future clients, generation, billing, feed, partner cabinet, admin, and Telegram gateway.
- [`../OPERATIONAL_FLOWS.md`](../OPERATIONAL_FLOWS.md) — onboarding, generation, provider callbacks, payments, publication, remix, broadcast, partner payout, and mirror failover flows.
- [`../SAFETY_COMPLIANCE.md`](../SAFETY_COMPLIANCE.md) — adult-content gate, moderation controls, immutable webhook logging, and high-risk operational constraints.
- [`../ROADMAP.md`](../ROADMAP.md) — phased implementation plan.
- [`../FRONTEND_RESET.md`](../FRONTEND_RESET.md) — accepted removal decision and requirements for a replacement frontend.

Russian documentation is available in [`../ru/`](../ru/README.md).

## External references

Implementation must be kept aligned with official/provider documentation:

- Kie Seedance 2.0: `https://docs.kie.ai/market/bytedance/seedance-2`
- Kie Seedream 5 Pro Text-to-Image: `https://docs.kie.ai/market/seedream/5-pro-text-to-image`
- Kie Seedream 5 Pro Image-to-Image: `https://docs.kie.ai/market/seedream/5-pro-image-to-image`
- Telegram Mini Apps: `https://core.telegram.org/bots/webapps`
- Telegram Stars for digital goods/services: `https://core.telegram.org/bots/payments-stars`
- CrocoPay developer docs: `https://crocopay.tech/developer?type=express`

## Language maintenance rule

When changing product architecture, model capabilities, billing, moderation, or public API contracts, update both the English and Russian documentation layers in the same PR.
