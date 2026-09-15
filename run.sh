#!/bin/bash
# Launcher for terminal_chart.py: sets up the virtual environment, then passes
# every option through; defaults and --help come from terminal_chart.py itself.

set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q --disable-pip-version-check -r requirements.txt

exec python3 terminal_chart.py "$@"
