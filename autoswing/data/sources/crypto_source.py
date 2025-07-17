from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta
import pandas as pd
import ccxt

# simple parse ("3y","90d")
def _parse_hist_window(window: str) -> int:
    w = window.lower().strip()
    if w.endswith("y"):
        return int(w[:-1]) * 365
    if w.endswith("mo"):
        return int(w[:-2]) * 30
    if w.endswith("d"):
        return int(w[:-1])
    return int(w)

def _date_range(days: int):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    return int(start.timestamp()*1000), int(end.timestamp()*1000)  # ms

def _fetch_ohlcv(exchange, symbol: str, since_ms: int, limit: int = 1000):
    bars = []
    fetch = getattr(exchange, "fetch_ohlcv", None)
    if fetch is None:
        return []
    timeframe = "1d"
    ms = since_ms
    while True:
        try:
            batch = fetch(symbol, timeframe=timeframe, since=ms, limit=limit)
        except Exception:
            break
        if not batch:
            break
        bars.extend(batch)
        last_ts = batch[-1][0]
        if last_ts <= ms:
            break
        ms = last_ts + 24*3600*1000
        if len(batch) < limit:
            break
    return bars

def _to_df(raw) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame()
    df = pd.DataFrame(raw, columns=["ts","open","high","low","close","volume"])
    df["date"] = pd.to_datetime(df["ts"], unit="ms")
    return df[["date","open","high","low","close","volume"]]

def fetch_crypto_daily(pair: str, history: str, prefer: str = "binanceus") -> Optional[pd.DataFrame]:
    """Return daily OHLCV DataFrame in USD quote. pair like 'BTC/USD' or 'BTCUSD'."""
    pair_norm = pair.upper().replace("USDT","USD").replace("USDUSD","USD")
    if "/" not in pair_norm:
        # assume base+quote w/out slash
        if pair_norm.endswith("USD"):
            pair_norm = pair_norm[:-3] + "/USD"
        else:
            pair_norm = pair_norm + "/USD"

    days = _parse_hist_window(history)
    since_ms, _ = _date_range(days)

    exchanges = []
    if prefer == "binanceus":
        exchanges = [ccxt.binanceus(), ccxt.kraken()]
    else:
        exchanges = [ccxt.kraken(), ccxt.binanceus()]

    for ex in exchanges:
        try:
            if pair_norm not in ex.symbols:
                ex.load_markets()
            sym = pair_norm if pair_norm in ex.symbols else pair_norm.replace("/USD","/USDT")
            raw = _fetch_ohlcv(ex, sym, since_ms)
            df = _to_df(raw)
            if len(df):
                return df
        except Exception:
            continue
    return None
