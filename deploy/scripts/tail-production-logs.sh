#!/usr/bin/env sh
set -eu

COMPOSE_FILE=${COMPOSE_FILE:-compose.production.yml}
ENV_FILE=${ENV_FILE:-.env.production}
SERVICE=${1:-}

if [ -n "$SERVICE" ]; then
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" logs -f --tail=200 "$SERVICE"
else
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" logs -f --tail=200
fi
