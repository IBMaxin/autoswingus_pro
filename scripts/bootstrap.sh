#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

log()  { echo "[bootstrap] $*"; }
warn() { echo "[bootstrap][WARN] $*" >&2; }
err()  { echo "[bootstrap][ERR] $*" >&2; }

# ---- venv ----
if [ ! -d .venv ]; then
  log "creating venv"
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel >/dev/null

# ---- requirements ----
if [ ! -f requirements.txt ]; then
  warn "requirements.txt missing; creating minimal"
  cat > requirements.txt <<'RQR'
pandas==2.2.2
numpy==1.26.4
PyYAML==6.0.2
pydantic==2.8.2
python-dotenv==1.0.1
httpx==0.27.0
requests==2.32.3
alpaca-py==0.21.0
SQLAlchemy==2.0.31
rich==13.7.1
matplotlib==3.9.0
pytest==8.3.1
pre-commit==3.7.1
ruff==0.5.6
mypy==1.10.0
typer==0.12.3
click==8.1.7
pyarrow==16.1.0
yfinance==0.2.40
RQR
fi

log "installing requirements"
pip install -r requirements.txt >/dev/null

# ---- .env ----
if [ ! -f .env ]; then
  warn ".env missing; copying example"
  cp .env.example .env || touch .env
  chmod 600 .env || true
fi

# ---- configs ----
mkdir -p autoswing/config
if [ ! -f autoswing/config/accounts.yaml ]; then
  log "writing default accounts.yaml"
  cat > autoswing/config/accounts.yaml <<'ACCTS'
accounts:
  alpaca_paper:
    broker: alpaca
    type: cash
    key_id: ${ALPACA_PAPER_KEY}
    secret_key: ${ALPACA_PAPER_SECRET}
    base_url: ${ALPACA_PAPER_BASE_URL}
    data_source: alpaca
    starting_cash: 1000
  papercash_sim:
    broker: papercash
    type: cash
    starting_cash: 1000
    data_source: csv
ACCTS
fi

if [ ! -f autoswing/config/settings_default.yaml ]; then
  log "writing default settings_default.yaml"
  cat > autoswing/config/settings_default.yaml <<'SETT'
timeframe: 1d
run_schedule: after_close
universe: [AAPL, MSFT, NVDA, TSLA, IWM, SPY]
risk_per_trade: 0.02
max_positions: 5
enforce_cash_settlement: true
warn_pdt_trades: true
default_order_type: limit
SETT
fi

# ---- pytest smoke ----
log "running pytest"
pytest -q || { err "pytest failed"; exit 1; }

log "bootstrap complete"
