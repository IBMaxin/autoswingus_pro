from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List

@dataclass
class CashEvent:
    trade_date: date
    settle_date: date
    amount: float   # +credit, -debit
    symbol: str
    note: str = ""

class CashLedger:
    """T+1 (default) settlement cash ledger."""
    def __init__(self, starting_cash: float, settlement_days: int = 1):
        self.starting_cash = float(starting_cash)
        self.settlement_days = settlement_days
        self.events: List[CashEvent] = []

    def record(self, trade_dt: date, amount: float, symbol: str, note: str = ""):
        self.events.append(
            CashEvent(
                trade_date=trade_dt,
                settle_date=trade_dt + timedelta(days=self.settlement_days),
                amount=float(amount),
                symbol=symbol,
                note=note,
            )
        )

    def settled_cash(self, on_dt: date) -> float:
        cash = self.starting_cash
        for ev in self.events:
            if ev.settle_date <= on_dt:
                cash += ev.amount
        return cash

    def unsettled_cash(self, on_dt: date) -> float:
        cash = 0.0
        for ev in self.events:
            if ev.settle_date > on_dt:
                cash += ev.amount
        return cash
