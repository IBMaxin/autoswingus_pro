from __future__ import annotations
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def _parse_hist_window(window: str) -> int:
    w = window.lower().strip()
    if w.endswith("y"):
        return int(w[:-1]) * 365
    if w.endswith("mo"):
        return int(w[:-2]) * 30
    if w.endswith("d"):
        return int(w[:-1])
    return int(w)

def fetch_yahoo_daily(symbol: str, history: str) -> pd.DataFrame | None:
    days = _parse_hist_window(history)
    end = datetime.utcnow().date()
    start = end - timedelta(days=days)
    df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
    if df is None or df.empty:
        return None
    df = df.reset_index()
    df.rename(columns={"Date": "date", "Open": "open", "High": "high",
                       "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)
    df["date"] = pd.to_datetime(df["date"])
    keep_cols = ["date", "open", "high", "low", "close", "volume"]
    return df[keep_cols]
