# AutoSwingUS-Pro

Cash-account–aware, Freqtrade-inspired swing trading automation for U.S. equities.

## Features (planned)
- Cash ledger tracks T+1 settlement; blocks freeride violations.
- PDT warning counter.
- Alpaca API (paper + live) + offline PaperCash simulator.
- Strategy plugin API (scan, size, manage, exit).
- Backtest + live modes.
- Streamlit dashboard.

## Quickstart
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add keys
pytest -q
---

### 5.4 Package Skeleton Files
We’ll create minimal importable modules so `pytest` and `python -c "import autoswing"` succeed.

> **All commands below assume you are in `~/autoswingus_pro`.**

#### 5.4.1 `autoswing/__init__.py`
```bash
cat > autoswing/__init__.py <<'EOF'
"""AutoSwingUS-Pro package root."""
__version__ = "0.0.1"
# assistant patch smoke Thu Jul 17 08:20:39 AM PDT 2025
