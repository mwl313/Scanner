#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="${ROOT_DIR}/logs/cloudflared.pid"

if [[ -f "${PID_FILE}" ]]; then
  PID="$(cat "${PID_FILE}")"
  if kill -0 "${PID}" 2>/dev/null; then
    kill "${PID}"
    echo "Stopped quick tunnel (pid ${PID})."
  else
    echo "No running process for pid ${PID}."
  fi
  rm -f "${PID_FILE}"
  exit 0
fi

if pkill -f "cloudflared tunnel --url http://127.0.0.1:8080" 2>/dev/null; then
  echo "Stopped quick tunnel process."
else
  echo "No quick tunnel process found."
fi
