#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${ROOT_DIR}/backups"
TS="$(date +%Y%m%d_%H%M%S)"

mkdir -p "${BACKUP_DIR}"

DB_NAME="$(grep '^POSTGRES_DB=' "${ROOT_DIR}/.env" | cut -d= -f2-)"
DB_USER="$(grep '^POSTGRES_USER=' "${ROOT_DIR}/.env" | cut -d= -f2-)"

docker compose -f "${ROOT_DIR}/docker-compose.yml" --env-file "${ROOT_DIR}/.env" \
  exec -T db pg_dump -U "${DB_USER}" -d "${DB_NAME}" > "${BACKUP_DIR}/scanner_${TS}.sql"

gzip -f "${BACKUP_DIR}/scanner_${TS}.sql"
echo "Backup written: ${BACKUP_DIR}/scanner_${TS}.sql.gz"
