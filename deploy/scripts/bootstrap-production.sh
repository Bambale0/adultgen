#!/usr/bin/env sh
set -eu

COMPOSE_FILE=${COMPOSE_FILE:-compose.production.yml}
ENV_FILE=${ENV_FILE:-.env.production}

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE. Copy .env.production.example and fill real secrets." >&2
  exit 1
fi

if grep -q "CHANGE_ME" "$ENV_FILE"; then
  echo "$ENV_FILE still contains CHANGE_ME placeholders." >&2
  exit 1
fi

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d postgres redis minio minio-init
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up --exit-code-from migrate migrate
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d api web edge

echo "AdultGen production stack started. Run deploy/scripts/healthcheck-production.sh to verify."
