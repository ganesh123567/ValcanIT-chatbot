#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/infra/docker/docker-compose.ec2.yml"
ENV_FILE="$ROOT_DIR/infra/env/ec2.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE"
  echo "Create it from infra/env/ec2.env.example and update ALLOWED_ORIGINS before deploying."
  exit 1
fi

cd "$ROOT_DIR"

docker compose -f "$COMPOSE_FILE" up -d --build ollama

for attempt in {1..30}; do
  if docker compose -f "$COMPOSE_FILE" exec -T ollama ollama list >/dev/null 2>&1; then
    break
  fi
  if [ "$attempt" -eq 30 ]; then
    echo "Ollama did not become ready in time." >&2
    exit 1
  fi
  sleep 2
done

docker compose -f "$COMPOSE_FILE" exec -T ollama ollama pull "$(grep '^OLLAMA_MODEL=' "$ENV_FILE" | cut -d= -f2-)"
docker compose -f "$COMPOSE_FILE" exec -T ollama ollama pull "$(grep '^OLLAMA_EMBED_MODEL=' "$ENV_FILE" | cut -d= -f2-)"
docker compose -f "$COMPOSE_FILE" up -d --build api

echo "Deployment complete."
echo "Health check: curl http://localhost:8000/health"
