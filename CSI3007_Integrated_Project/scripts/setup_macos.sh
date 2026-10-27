#!/usr/bin/env bash
# CSI3007 Integrated Project - macOS/Linux setup script
# Course: CSI3007 Advanced Python Programming
# Run from the repository root:  bash scripts/setup_macos.sh

set -euo pipefail

echo "=== CSI3007 Integrated Project - macOS setup ==="

# 1. Python check (3.11+ expected; Homebrew python3 works fine)
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found. Install via 'brew install python' or from https://www.python.org/downloads/" >&2
    exit 1
fi
echo "Found $(python3 --version)"

# 2. Virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# 3. Dependencies
echo "Installing pinned dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 4. Per-project .env files from templates (idempotent)
for project in \
    person_a_sachien_n_23MID0255 \
    person_b_shravan_n_a_23MID0445 \
    person_c_hariharan_s_23MID0182
do
    if [ -f "$project/.env.example" ] && [ ! -f "$project/.env" ]; then
        cp "$project/.env.example" "$project/.env"
        echo "Created $project/.env from template"
    fi
done

# 5. Root .env for the gateway (optional)
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created root .env from template"
fi

# 6. Syntax sanity check
echo "Verifying Python syntax of all project modules..."
python -m compileall -q person_a_sachien_n_23MID0255 person_b_shravan_n_a_23MID0445 \
    person_c_hariharan_s_23MID0182 integration shared
echo "Syntax OK"

echo
echo "Setup complete. Start everything with:"
echo "  .venv/bin/python start_all.py"
echo "or use: bash scripts/start_macos.sh"
