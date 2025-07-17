"""Portfolio + cash ledger (Phase 1 stub)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Position:
    symbol: str
    qty: int
    avg_price: float


@dataclass
class Portfolio:
    cash: float = 0.0
    positions: Dict[str, Position] = field(default_factory=dict)

    @property
    def settled_cash(self) -> float:
        # Phase 1: no unsettled tracking yet
        return float(self.cash)

    def equity(self) -> float:
        # mark-to-cost
        pos_val = sum(p.qty * p.avg_price for p in self.positions.values())
        return float(self.cash + pos_val)
