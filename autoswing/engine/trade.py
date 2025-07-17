from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Position:
    symbol: str
    qty: int
    avg_price: float
    entry_dt: date

@dataclass
class Trade:
    trade_id: int
    dt: date
    symbol: str
    side: str   # 'buy'|'sell'
    qty: int
    price: float
    notional: float
    fee: float
    settle_dt: date
    settled: bool
    realized_pnl: float
    cash_after: float
