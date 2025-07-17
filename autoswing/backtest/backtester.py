"""Minimal backtest stub."""
from __future__ import annotations
import pandas as pd
from autoswing.engine.portfolio import Portfolio, Position

def run_backtest(data_bundle, strategy, starting_cash=1000.0):
    pf = Portfolio(cash=starting_cash)
    signals = strategy.scan(data_bundle)
    for sig in signals:
        if sig.action != "buy":
            continue
        price = data_bundle[sig.symbol].close.iloc[-1]
        size = strategy.position_size(pf, sig)
        if size <= 0:
            continue
        cost = size * price
        if cost <= pf.cash:
            pf.cash -= cost
            pf.positions[sig.symbol] = Position(sig.symbol, size, price)
    return pf
