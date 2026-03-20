#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.yml"
ENV_FILE="${ROOT_DIR}/.env"
BACKUP_SCRIPT="${ROOT_DIR}/scripts/backup_postgres.sh"

REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"
SKIP_BACKUP="false"

if [[ "${1:-}" == "--skip-backup" ]]; then
  SKIP_BACKUP="true"
fi

echo "[update] Root: ${ROOT_DIR}"
echo "[update] Target: ${REMOTE}/${BRANCH}"

if ! command -v git >/dev/null 2>&1; then
  echo "[update] ERROR: git is not installed."
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[update] ERROR: docker is not installed or not in PATH."
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "[update] ERROR: curl is not installed."
  exit 1
fi

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "[update] ERROR: missing ${COMPOSE_FILE}"
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[update] ERROR: missing ${ENV_FILE}"
  exit 1
fi

cd "${ROOT_DIR}"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "[update] WARN: git working tree is not clean."
  echo "[update] WARN: pull may fail if local tracked files conflict."
fi

if [[ "${SKIP_BACKUP}" != "true" ]]; then
  if [[ -x "${BACKUP_SCRIPT}" ]]; then
    echo "[update] Running DB backup..."
    "${BACKUP_SCRIPT}"
  else
    echo "[update] WARN: backup script not found/executable, skipping backup."
  fi
else
  echo "[update] Skipping backup (--skip-backup)."
fi

OLD_HEAD="$(git rev-parse HEAD)"

echo "[update] Fetching latest commits..."
git fetch "${REMOTE}" "${BRANCH}"

echo "[update] Pulling code..."
git pull --ff-only "${REMOTE}" "${BRANCH}"

NEW_HEAD="$(git rev-parse HEAD)"
if [[ "${OLD_HEAD}" != "${NEW_HEAD}" ]]; then
  if git diff --name-only "${OLD_HEAD}" "${NEW_HEAD}" | rg -q '^.env.example$'; then
    echo "[update] NOTICE: .env.example changed. Review and sync new keys into .env if needed."
  fi
else
  echo "[update] No new commits."
fi

echo "[update] Rebuilding/restarting containers..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --build

echo "[update] Container status:"
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps

echo "[update] Health check:"
curl -fsS --max-time 10 http://127.0.0.1:8080/health
echo

if command -v tailscale >/dev/null 2>&1; then
  echo "[update] Tailscale Serve status:"
  tailscale serve status || true
  echo "[update] Tailscale Funnel status:"
  tailscale funnel status || true
fi

echo "[update] Done."
