#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
LOG_FILE="${LOG_DIR}/cloudflared.log"
PID_FILE="${LOG_DIR}/cloudflared.pid"
TARGET_URL="http://127.0.0.1:8080"

mkdir -p "${LOG_DIR}"

if [[ -f "${PID_FILE}" ]] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
  echo "Quick tunnel already running (pid $(cat "${PID_FILE}"))."
  exit 0
fi

nohup cloudflared tunnel --url "${TARGET_URL}" --no-autoupdate >"${LOG_FILE}" 2>&1 < /dev/null &
PID="$!"
echo "${PID}" > "${PID_FILE}"
sleep 2
if ! kill -0 "${PID}" 2>/dev/null; then
  echo "Failed to start quick tunnel. Check ${LOG_FILE}."
  exit 1
fi

for _ in {1..30}; do
  if URL="$(rg -o 'https://[-a-z0-9]+\.trycloudflare\.com' "${LOG_FILE}" -m1 2>/dev/null)"; then
    if [[ -n "${URL}" ]]; then
      echo "Quick tunnel URL: ${URL}"
      exit 0
    fi
  fi
  sleep 1
done

echo "Tunnel started but URL not found yet. Check ${LOG_FILE}."
