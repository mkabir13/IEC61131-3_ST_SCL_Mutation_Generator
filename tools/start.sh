#!/bin/bash
# start.sh -- one-command launcher for the ST Mutation Dashboard.
#
# Usage:
#   ./start.sh                          # binds to 0.0.0.0:5050 (reachable on your LAN)
#   DASHBOARD_PORT=8080 ./start.sh      # different port
#   DASHBOARD_HOST=127.0.0.1 ./start.sh # local-only access
#
# First run creates a venv (tools/.venv) and installs dependencies;
# every run after that reuses it, so startup after the first time is fast.

set -e
cd "$(dirname "$0")"   # always run relative to this script's own directory (tools/)

if [ ! -f ".venv/bin/activate" ]; then
  if [ -d ".venv" ]; then
    echo "[start.sh] Found a .venv/ directory but it's missing bin/activate --"
    echo "            looks like an incomplete venv from an earlier run. Rebuilding it."
    rm -rf .venv
  else
    echo "[start.sh] No venv found -- creating tools/.venv (first run only)..."
  fi

  if ! python3 -m venv .venv; then
    echo "[start.sh] ERROR: 'python3 -m venv .venv' failed."
    echo "            On Debian/Ubuntu this is usually a missing package:"
    echo "                sudo apt install python3-venv"
    echo "            Then run ./start.sh again."
    exit 1
  fi

  if [ ! -f ".venv/bin/activate" ]; then
    echo "[start.sh] ERROR: venv creation reported success but .venv/bin/activate"
    echo "            still doesn't exist. This can happen inside some conda/"
    echo "            pyenv environments. Try removing tools/.venv manually and"
    echo "            creating it outside any active conda env, or run:"
    echo "                python3 -m venv --without-pip .venv && .venv/bin/python -m ensurepip"
    exit 1
  fi
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "[start.sh] Ensuring dependencies are installed..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

MATIEC_PATH="${MATIEC_BIN:-../matiec/iec2c}"
if [ ! -f "$MATIEC_PATH" ]; then
  echo "[start.sh] WARNING: MATIEC binary not found at $MATIEC_PATH"
  echo "            The dashboard needs a built MATIEC binary there (or set"
  echo "            MATIEC_BIN to point at yours). It will still start, but"
  echo "            every compile check will fail until this is fixed."
fi

export DASHBOARD_HOST="${DASHBOARD_HOST:-0.0.0.0}"
export DASHBOARD_PORT="${DASHBOARD_PORT:-5050}"

LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}')

echo ""
echo "=================================================================="
echo " ST Mutation Dashboard"
echo "=================================================================="
echo " Local:   http://127.0.0.1:${DASHBOARD_PORT}"
if [ -n "$LAN_IP" ] && [ "$DASHBOARD_HOST" = "0.0.0.0" ]; then
  echo " Network: http://${LAN_IP}:${DASHBOARD_PORT}"
fi
echo " Press Ctrl+C to stop."
echo "=================================================================="
echo ""

python3 run_dashboard.py
