"""Simple SMA pullback example (Phase 1 placeholder)."""
from __future__ import annotations
import pandas as pd
from autoswing.strategies.base_strategy import BaseStrategy, Signal


class SMAPullbackStrategy(BaseStrategy):
    timeframe = "1d"
    warmup_bars = 30

    def scan(self, data_bundle):
        signals = []
        for sym, df in data_bundle.items():
            # require close column
            if "close" not in df.columns:
                continue
            if len(df) < self.warmup_bars:
                continue
            sma20 = df.close.rolling(20).mean()
            sma50 = df.close.rolling(50).mean()
            # only act if enough bars for both
            if sma20.isna().iloc[-1] or sma50.isna().iloc[-1]:
                continue
            if sma20.iloc[-1] > sma50.iloc[-1]:
                # bullish; buy mild pullback
                if df.close.iloc[-1] < sma20.iloc[-1] * 0.995:
                    signals.append(Signal(sym, "buy", float(df.close.iloc[-1])))
        return signals

    def position_size(self, account, signal):
        # account is a Portfolio in Phase 1
        cash = getattr(account, "cash", 0.0)
        if cash <= 0:
            return 0
        alloc = cash / self.max_positions
        return int(alloc // signal.price)
