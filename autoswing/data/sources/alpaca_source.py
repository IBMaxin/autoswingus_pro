from __future__ import annotations
import os
from datetime import datetime, timedelta
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

def _parse_hist_window(window: str) -> int:
    w = window.lower().strip()
    if w.endswith("y"):  return int(w[:-1]) * 365
    if w.endswith("mo"): return int(w[:-2]) * 30
    if w.endswith("d"):  return int(w[:-1])
    return int(w)

def _date_range_from_hist(days: int):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    return start, end

def fetch_alpaca_daily(symbol: str, history: str) -> pd.DataFrame | None:
    load_dotenv(override=False)
    key = os.getenv("ALPACA_PAPER_KEY") or os.getenv("ALPACA_LIVE_KEY")
    sec = os.getenv("ALPACA_PAPER_SECRET") or os.getenv("ALPACA_LIVE_SECRET")
    if not key or not sec:
        return None
    client = StockHistoricalDataClient(api_key=key, secret_key=sec)
    days = _parse_hist_window(history)
    start, end = _date_range_from_hist(days)
    req = StockBarsRequest(symbol_or_symbols=symbol.upper(), timeframe=TimeFrame.Day, start=start, end=end)
    bars = client.get_stock_bars(req)
    if bars.df.empty:
        return None
    df = bars.df.reset_index()
    df = df[df["symbol"] == symbol.upper()].copy()
    df.rename(columns={"timestamp":"date"}, inplace=True)
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    keep = ["date","open","high","low","close","volume"]
    return df[keep]
