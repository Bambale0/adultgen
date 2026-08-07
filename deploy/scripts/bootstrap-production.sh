#!/usr/bin/env sh
set -eu

COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.production.yml}
ENV_FILE=${ENV_FILE:-.env.production}

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE. Copy deploy/env/production.env.example and fill real secrets." >&2
  exit 1
fi

if grep -Eiq "change-me|replace-me" "$ENV_FILE"; then
  echo "$ENV_FILE still contains placeholder secrets." >&2
  exit 1
fi

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d postgres redis minio
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" --profile setup run --rm create-buckets
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" --profile migrate run --rm migrate
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d backend studio nginx

echo "AdultGen production stack started. Run deploy/scripts/healthcheck-production.sh to verify."
