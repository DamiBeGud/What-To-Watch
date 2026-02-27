#!/bin/sh
set -eu

cd /workspace

ARTIFACTS_DIR="${ARTIFACTS_DIR:-artifacts}"
APP_FILE="${STREAMLIT_APP_FILE:-streamlit_app.py}"
PORT="${STREAMLIT_SERVER_PORT:-8501}"

if [ "${RUN_STARTUP_VALIDATION:-1}" = "1" ]; then
  python -m src.infrastructure.loaders.startup_validator --artifacts-dir "${ARTIFACTS_DIR}"
fi

if [ ! -f "${APP_FILE}" ]; then
  if [ -f "app/main.py" ]; then
    APP_FILE="app/main.py"
  else
    echo "Missing Streamlit app entrypoint." >&2
    echo "Expected one of: /workspace/streamlit_app.py or /workspace/app/main.py" >&2
    echo "Next step: implement Task 8 Streamlit app scaffolding, then rerun the container." >&2
    exit 1
  fi
fi

exec streamlit run "${APP_FILE}" \
  --server.address=0.0.0.0 \
  --server.port="${PORT}" \
  --server.headless=true

