#!/usr/bin/env bash

# Seed default AI prompts inside the backend container.
# Usage: ./scripts/seed_prompts.sh [dev|prod]

set -euo pipefail

MODE="${1:-dev}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker &>/dev/null; then
  echo "Docker is not installed. Please install Docker first." >&2
  exit 1
fi

if docker compose version &>/dev/null; then
  COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
  COMPOSE_CMD="docker-compose"
else
  echo "Docker Compose is not installed." >&2
  exit 1
fi

case "$MODE" in
  dev)
    COMPOSE_FILE=""
    SERVICE="backend"
    ;;
  prod)
    COMPOSE_FILE="-f docker-compose.prod.yml"
    SERVICE="backend"
    ;;
  *)
    echo "Unknown mode: $MODE (expected 'dev' or 'prod')" >&2
    exit 1
    ;;
esac

echo "Seeding prompts using mode: $MODE"
$COMPOSE_CMD $COMPOSE_FILE exec "$SERVICE" python seed_prompts.py
