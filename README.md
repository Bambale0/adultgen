# Experimental AI Media Platform

> 🚧 **Architecture scaffold / work in progress**
>
> This repository is an experimental product architecture and is **not one of the main portfolio projects** on this profile.
>
> Repository codename: `adultgen`.

The project explores a backend-first architecture for a Telegram-first AI media product with replaceable channel adapters, generation workflows, internal credits, partner accounting and moderation.

## Current status

The repository currently contains architecture documentation and an initial Python scaffold. It should be read as design/development work rather than a finished production system.

## Architecture direction

- backend-first product boundary;
- replaceable Telegram gateway clients;
- canonical user identity independent of a specific bot;
- append-only wallet/ledger concepts;
- immutable capture of payment webhook events before processing;
- explicit provider/model capability contracts;
- temporary-vs-published media lifecycle;
- moderation and consent boundaries;
- generation worker and Mini App flows planned around documented API contracts.

## Repository structure

```text
docs/                 # architecture, API contracts, data model and roadmap
src/adultgen/         # initial Python application/domain scaffold
docker-compose.yml    # local infrastructure
.env.example          # configuration contract without real credentials
```

## Development

```bash
cp .env.example .env
docker compose up -d
uvicorn adultgen.apps.core_api:app --reload
```

## Status note

Implementation is incomplete and interfaces may change. For production-ready examples, see the completed application repositories on this GitHub profile.
