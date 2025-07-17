"""Base strategy interface."""
from __future__ import annotations

class Signal:
    def __init__(self, symbol, action, price, stop=None, tags=None):
        self.symbol = symbol
        self.action = action
        self.price = price
        self.stop = stop
        self.tags = tags or {}

class BaseStrategy:
    timeframe = "1d"
    warmup_bars = 50
    max_positions = 5
    risk_per_trade = 0.02

    def scan(self, data_bundle):  # override
        return []

    def position_size(self, account, signal):
        return 0
