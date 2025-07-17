"""Paper execution + cash ledger support for AutoSwingUS‑Pro.

Phase 3A refactor: A single class, :class:`PaperAccount`, handles portfolio
positions, cash ledger (T+1 default), and simplified bar‑close fills used by
our daily backtester.  Historically we had a separate *PaperExecutor*; for
backward compatibility we now alias::

    PaperExecutor = PaperAccount

The module also exposes `run_bar_backtest()` which the CLI and UI call to run a
lightweight, cash‑account‑aware daily backtest across a bundle of symbols.
"""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional
import math

import pandas as pd

from autoswing.engine.ledger import CashLedger
from autoswing.engine.trade import Position, Trade
from autoswing.io.trade_log import append_trades


class PaperAccount:
    """In‑memory account used for backtest / paper‑run.

    Tracks a :class:`CashLedger` for settlement, open positions, and a running
    cash value (includes unsettled debits). Provides *buy*/*sell* helpers that
    mutate state and emit :class:`Trade` records.
    """
    def __init__(self, starting_cash: float, settlement_days: int = 1):
        self.ledger = CashLedger(starting_cash, settlement_days)
        self.positions: Dict[str, Position] = {}
        self._next_trade_id = 1
        self.cash_running = float(starting_cash)  # includes unsettled debits

    # --- util -------------------------------------------------------------
    def _trade_id(self) -> int:
        i = self._next_trade_id
        self._next_trade_id += 1
        return i

    def settled_cash(self, dt: Optional[date] = None) -> float:
        """Cash settled as of *dt* (default today)."""
        if dt is None:
            dt = date.today()
        return self.ledger.settled_cash(dt)

    # --- fills ------------------------------------------------------------
    def buy(self, dt: date, symbol: str, price: float, qty: int, fee: float = 0.0):
        notional = price * qty
        self.cash_running -= (notional + fee)
        self.ledger.record(dt, -(notional + fee), symbol, note="buy")
        if symbol in self.positions:
            p = self.positions[symbol]
            new_qty = p.qty + qty
            new_avg = ((p.avg_price * p.qty) + (price * qty)) / new_qty
            self.positions[symbol] = Position(symbol, new_qty, new_avg, p.entry_dt)
        else:
            self.positions[symbol] = Position(symbol, qty, price, dt)
        tr = Trade(
            trade_id=self._trade_id(), dt=dt, symbol=symbol, side="buy",
            qty=qty, price=price, notional=notional, fee=fee,
            settle_dt=dt, settled=False, realized_pnl=0.0,
            cash_after=self.cash_running,
        )
        return tr

    def sell(self, dt: date, symbol: str, price: float, qty: Optional[int] = None, fee: float = 0.0):
        if symbol not in self.positions:
            return None
        p = self.positions[symbol]
        if qty is None or qty > p.qty:
            qty = p.qty
        notional = price * qty
        self.cash_running += (notional - fee)
        self.ledger.record(dt, +(notional - fee), symbol, note="sell")
        realized = (price - p.avg_price) * qty
        if qty == p.qty:
            del self.positions[symbol]
        else:
            self.positions[symbol] = Position(symbol, p.qty - qty, p.avg_price, p.entry_dt)
        tr = Trade(
            trade_id=self._trade_id(), dt=dt, symbol=symbol, side="sell",
            qty=qty, price=price, notional=notional, fee=fee,
            settle_dt=dt, settled=False, realized_pnl=realized,
            cash_after=self.cash_running,
        )
        return tr


# ---------------------------------------------------------------------------
# Sizing helper (percent of settled cash)
# ---------------------------------------------------------------------------

def percent_cash_size(account: PaperAccount, dt: date, price: float, pct: float, max_positions: int) -> int:
    settled = account.settled_cash(dt)
    slots = max(1, max_positions - len(account.positions))
    alloc_cash = settled * pct
    alloc_cash = min(alloc_cash, settled / slots)
    qty = int(math.floor(alloc_cash / price))
    return max(qty, 0)


# ---------------------------------------------------------------------------
# Daily bar backtest loop
# ---------------------------------------------------------------------------

def run_bar_backtest(
    bundle: Dict[str, pd.DataFrame],
    strategy,
    starting_cash: float,
    mark_to_close: bool = True,
    max_hold_days: Optional[int] = None,
    fee_per_share: float = 0.0,
    project_root=None,
):
    """Simple daily bar backtest across *bundle*.

    Strategy expected to provide:
    - ``alloc_pct`` (0‑1) percent of settled cash per entry
    - ``max_positions`` (int)
    - ``scan(slice_bundle)`` -> iterable of signal objects with ``.symbol`` and ``.action``
    """
    idx = sorted(set().union(*[pd.to_datetime(df["date"]).dt.date.tolist() for df in bundle.values()]))
    acct = PaperAccount(starting_cash, settlement_days=1)
    trades = []

    data_sorted = {s: df.sort_values("date").reset_index(drop=True) for s, df in bundle.items()}

    for i, dt in enumerate(idx):
        # slice up to current date for each symbol
        slice_bundle = {}
        for sym, df in data_sorted.items():
            mask = pd.to_datetime(df["date"]).dt.date <= dt
            sdf = df.loc[mask].copy()
            if not sdf.empty:
                slice_bundle[sym] = sdf

        # timed exits
        if max_hold_days is not None:
            for sym, pos in list(acct.positions.items()):
                held = (dt - pos.entry_dt).days
                if held >= max_hold_days:
                    sdf = slice_bundle.get(sym)
                    if sdf is not None:
                        px = float(sdf["close"].iloc[-1])
                        tr = acct.sell(dt, sym, px, fee=fee_per_share * pos.qty)
                        if tr:
                            trades.append(tr.__dict__)

        # generate new buy signals
        sigs = strategy.scan(slice_bundle)
        for sig in sigs:
            if sig.action != "buy":
                continue
            sdf = slice_bundle.get(sig.symbol)
            if sdf is None or sdf.empty:
                continue
            px = float(sdf["close"].iloc[-1])
            qty = percent_cash_size(acct, dt, px, pct=strategy.alloc_pct, max_positions=strategy.max_positions)
            if qty <= 0:
                continue
            tr = acct.buy(dt, sig.symbol, px, qty, fee=fee_per_share * qty)
            trades.append(tr.__dict__)

    # mark final equity
    mark_prices = {s: float(df["close"].iloc[-1]) for s, df in data_sorted.items()}
    final_eq = acct.equity(mark_prices, idx[-1]) if idx else starting_cash

    if project_root is not None and trades:
        append_trades(trades, project_root)

    return final_eq, trades, acct


# ------------------------------------------------------------------
# Backward‑compat shim: legacy name used in earlier phases
# ------------------------------------------------------------------
PaperExecutor = PaperAccount  # alias (inherits not needed)
