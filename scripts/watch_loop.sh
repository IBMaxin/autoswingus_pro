#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$HOME/autoswingus_pro"
LOG_DIR="$PROJECT_ROOT/runtime/logs"
mkdir -p "$LOG_DIR"
cd "$PROJECT_ROOT"

while true; do
  TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  echo "[$TS] === AutoSwing watch loop ==="

  # pull latest
  git fetch origin >/dev/null 2>&1 || true
  git pull --rebase origin main || echo "[WARN] git pull failed"

  # activate venv
  if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
  fi

  # smoke tests
  pytest -q || echo "[WARN] pytest failed"

  # fast backtest (short lookback; faster)
  python -m autoswing.cli paper-backtest --days 60 || echo "[WARN] backtest failed"

  # run montecarlo for sanity
  python -m autoswing.cli montecarlo --iters 500 --start 1000 || echo "[WARN] mc failed"

  # log to file
  echo "[$TS] cycle done" >> "$LOG_DIR/watch_loop.log"
  sleep 600  # 10 minutes
done
