from __future__ import annotations
import random
from pathlib import Path
from typing import Iterable, List
import pandas as pd

ROOT = Path(__file__).parents[2]

def _load_trade_pnls_from_logs() -> list[float]:
    """Read trade logs under runtime/logs/trades_*.csv; assume 0 PnL placeholder."""
    tdir = ROOT / "runtime" / "logs"
    vals: List[float] = []
    if not tdir.exists():
        return vals
    for f in tdir.glob("trades_*.csv"):
        try:
            df = pd.read_csv(f)
            # placeholder: treat each trade as 0% (improve later when exits implemented)
            vals.extend([0.0] * len(df))
        except Exception:
            continue
    return vals

def bootstrap_pnl(
    trade_pnls: Iterable[float] | None = None,
    iters: int = 5000,
    starting_cash: float = 1000.0,
) -> dict:
    """Bootstrap Monte Carlo on trade PnL dollars (additive)."""
    if trade_pnls is None:
        trade_pnls = _load_trade_pnls_from_logs()
    trade_pnls = list(trade_pnls)
    if not trade_pnls:
        trade_pnls = [0.0]
    finals: List[float] = []
    for _ in range(iters):
        total = starting_cash
        for pnl in random.choices(trade_pnls, k=len(trade_pnls)):
            total += pnl
        finals.append(total)
    finals.sort()
    def pct(p): return finals[int(p*(len(finals)-1))]
    return {
        "iters": iters,
        "start": starting_cash,
        "min": finals[0],
        "p05": pct(0.05),
        "p50": pct(0.50),
        "p95": pct(0.95),
        "max": finals[-1],
    }
