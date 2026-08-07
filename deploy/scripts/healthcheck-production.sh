#!/usr/bin/env sh
set -eu

COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.production.yml}
ENV_FILE=${ENV_FILE:-.env.production}

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

BASE_URL=${BASE_URL:-http://127.0.0.1:${HTTP_PORT:-4444}}

curl -fsS "$BASE_URL/healthz" >/dev/null
curl -fsS "$BASE_URL/api/health" >/dev/null
curl -fsS "$BASE_URL/" | grep -q "AdultGen Studio"

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps

echo "AdultGen healthcheck passed for $BASE_URL"
