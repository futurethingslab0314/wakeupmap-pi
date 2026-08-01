#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"
mkdir -p "${LOG_DIR}"

USER_NAME_VALUE="${USER_NAME:-YuPie}"
USER_NAME_VALUE="$(printf '%s' "${USER_NAME_VALUE}" | tr '[:lower:]' '[:upper:]')"
export USER_NAME="${USER_NAME_VALUE}"

cd "${SCRIPT_DIR}"

echo "🌅 WakeUpMap Square launcher"
echo "📁 Working directory: ${SCRIPT_DIR}"
echo "👤 USER_NAME: ${USER_NAME}"

cleanup() {
  echo "🧹 Stopping WakeUpMap processes..."
  if [ -n "${SERVER_PID:-}" ]; then
    kill "${SERVER_PID}" 2>/dev/null || true
  fi
  if [ -n "${BRIDGE_PID:-}" ]; then
    kill "${BRIDGE_PID}" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

echo "🚀 Starting square server..."
npm start > "${LOG_DIR}/square-server.log" 2>&1 &
SERVER_PID=$!

sleep 4

echo "🔗 Starting hardware bridge..."
python3 pi_hardware_bridge.py > "${LOG_DIR}/pi-hardware-bridge.log" 2>&1 &
BRIDGE_PID=$!

echo "✅ WakeUpMap Square is running."
echo "   Server log: ${LOG_DIR}/square-server.log"
echo "   Bridge log: ${LOG_DIR}/pi-hardware-bridge.log"

wait "${SERVER_PID}" "${BRIDGE_PID}"
