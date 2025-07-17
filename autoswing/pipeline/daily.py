from __future__ import annotations
from pathlib import Path
from typing import Sequence
from autoswing.utils.env import load_env
from autoswing.config.loader import load_settings
from autoswing.data.fetch import fetch_history
from autoswing.data.loader import load_bundle_cached
from autoswing.strategies.sma_pullback import SMAPullbackStrategy
from autoswing.backtest.backtester import run_backtest

ROOT = Path(__file__).parents[2]

def run_pipeline(
    days: int = 60,
    symbols: Sequence[str] | None = None,
    sources: Sequence[str] = ("alpaca","yahoo"),
    starting_cash: float = 1000.0,
) -> float:
    """
    Minimal daily pipeline:
      1. Load env + settings.
      2. Determine symbol list (arg or settings.universe).
      3. Fetch/refresh history.
      4. Load last N days from cache.
      5. Run SMA pullback backtest (placeholder for live signals).
      6. Return portfolio equity.
    """
    load_env(ROOT / ".env")
    st = load_settings(ROOT / "autoswing" / "config" / "settings_default.yaml")
    if symbols is None:
        # prefer new universe_equities if present; else legacy universe
        syms = getattr(st, "universe_equities", None) or getattr(st, "universe", [])
    else:
        syms = [s.upper() for s in symbols]
    # fetch data (will append+dedupe cache)
    fetch_history(syms, history=f"{days}d", sources=sources, project_root=ROOT)
    # load N days
    bundle = load_bundle_cached(syms, days=days, project_root=ROOT)
    # run strat
    strat = SMAPullbackStrategy()
    pf = run_backtest(bundle, strat, starting_cash=starting_cash)
    return float(pf.equity())
