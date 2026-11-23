#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"

mkdir -p "${LOG_DIR}"

USER_NAME_VALUE="${USER_NAME:-YUPIE}"
USER_NAME_VALUE="$(printf '%s' "${USER_NAME_VALUE}" | tr '[:lower:]' '[:upper:]')"

export USER_NAME="${USER_NAME_VALUE}"

cd "${SCRIPT_DIR}"

echo "🌅 Launching Wakeup Map"
echo "📁 Working directory: ${SCRIPT_DIR}"
echo "👤 USER_NAME: ${USER_NAME}"

python3 main_web_dsi.py 2>&1 | tee "${LOG_DIR}/main-web-dsi.log"
