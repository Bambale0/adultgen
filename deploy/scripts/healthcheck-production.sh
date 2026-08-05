#!/usr/bin/env sh
set -eu

BASE_URL=${BASE_URL:-http://127.0.0.1}
COMPOSE_FILE=${COMPOSE_FILE:-compose.production.yml}
ENV_FILE=${ENV_FILE:-.env.production}

curl -fsS "$BASE_URL/healthz" >/dev/null
curl -fsS "$BASE_URL/api/health" >/dev/null

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

echo "AdultGen healthcheck passed for $BASE_URL"
