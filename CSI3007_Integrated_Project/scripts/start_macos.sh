#!/usr/bin/env bash
# CSI3007 Integrated Project - start script (macOS/Linux)
# Starts the three APIs, the integration gateway (landing page) and the three
# Streamlit dashboards. Press Ctrl+C to stop all services.

set -euo pipefail
cd "$(dirname "$0")/.."   # repository root

if [ -x ".venv/bin/python" ]; then
    PYTHON=.venv/bin/python
else
    PYTHON=python3
fi

exec "$PYTHON" start_all.py "$@"
