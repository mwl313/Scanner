#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="${ROOT_DIR}/logs/cloudflared.log"
PID_FILE="${ROOT_DIR}/logs/cloudflared.pid"

if [[ -f "${PID_FILE}" ]] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
  echo "Quick tunnel running (pid $(cat "${PID_FILE}"))."
else
  echo "Quick tunnel not running."
fi

if [[ -f "${LOG_FILE}" ]]; then
  URL="$(rg -o 'https://[-a-z0-9]+\.trycloudflare\.com' "${LOG_FILE}" -m1 || true)"
  if [[ -n "${URL}" ]]; then
    echo "URL: ${URL}"
  else
    echo "URL not found in log yet."
  fi
else
  echo "No log file at ${LOG_FILE}."
fi
