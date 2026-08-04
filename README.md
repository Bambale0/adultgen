# AdultGen

Telegram-first AI media generation platform with Mini App, multi-reference cinematic workflows, internal credits, partner payouts, moderation, global feed, and replaceable Telegram bot channels.

## Architecture direction

AdultGen is designed as a backend-first platform:

- Telegram bots are replaceable gateway clients.
- Canonical users are keyed by `telegram_user_id`, not by bot.
- Wallets use an append-only ledger.
- Payment webhooks are captured as immutable raw records before processing.
- Temporary generation media expires after 24 hours unless published.
- Published profile/feed media is stored permanently until user/admin deletion.
- Adult feed access requires 18+ consent and admin-controlled moderation.
- Model capabilities are explicit: Seedream and Seedance payloads are selected through scenario-specific provider capability rules, not a single generic generation form.

## MVP product scope

- Telegram bot + Mini App.
- Manual project and scene creation.
- Saved avatar photo sets.
- Seedream 5 Pro image generation/editing.
- Seedance 2.0 video generation with text-to-video, first-frame, first+last-frame, and multimodal reference workflows.
- Optional manually invoked AI Director.
- Parallel generation jobs.
- Internal credits and subscription plans.
- SharPay/CrocoPay adapters behind Billing Gateway.
- Partner program: 20% first payment, 5% follow-up payments for 90 days.
- Public/private user profiles.
- One global adult feed with likes, saves, remix, reports, and no comments.
- Admin panel for payments, feed, moderation, payouts, broadcasts, mirrors, and audit.

## Repository structure

```text
docs/
├── ARCHITECTURE.md
├── API_CONTRACTS.md
├── DATA_MODEL.md
├── MODEL_CAPABILITIES.md
├── OPERATIONAL_FLOWS.md
├── ROADMAP.md
└── SAFETY_COMPLIANCE.md

src/adultgen/
├── apps/
│   └── core_api.py
├── domain/
│   └── enums.py
└── config.py
```

## Local infrastructure

```bash
cp .env.example .env
docker compose up -d
```

Run Core API after installing dependencies:

```bash
uvicorn adultgen.apps.core_api:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

## Development status

Current branch contains the architecture baseline and initial Python scaffold. Implementation should proceed by phases in `docs/ROADMAP.md`.

Before implementing the generation worker or Mini App creation flow, read `docs/MODEL_CAPABILITIES.md`. It defines the exact Seedream/Seedance operation split, payload mapping, mutual exclusion rules, callback behavior, and provider validation requirements.
