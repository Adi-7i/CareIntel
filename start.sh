#!/usr/bin/env bash
# Start the API and, when configured, its worker and outbox dispatcher.
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -x .venv/bin/python ]]; then
    echo "Backend environment missing. Run ./setup_backend.sh first." >&2
    exit 1
fi
export PYTHONUNBUFFERED=1
exec .venv/bin/python scripts/backend_runtime.py start "$@"
