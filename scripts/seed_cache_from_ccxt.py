#!/usr/bin/env python
"""
Seed AutoSwing cache using CCXT OHLCV data (crypto).

Usage:
  python scripts/seed_cache_from_ccxt.py \
      --exchange binanceus \
      --pairs BTC/USDT,ETH/USDT \
      --timeframe 1d \
      --since 2022-01-01 \
      --alias-style noslash

Writes Parquet files to:
  runtime/data_cache/daily/<ALIAS>.parquet

If timeframe != 1d, data are resampled (UTC) to daily candles.
"""
from __future__ import annotations

import argparse
import sys
import time
import datetime as dt
from pathlib import Path
from typing import Iterable, List, Dict

import pandas as pd

try:
    import ccxt
except ImportError as e:  # pragma: no cover
    sys.exit("ccxt not installed; pip install ccxt")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = PROJECT_ROOT / "runtime" / "data_cache" / "daily"


# ------------------------------------------------------------------ helpers
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Seed AutoSwing cache from CCXT.")
    p.add_argument("--exchange", required=True, help="ccxt exchange id, e.g. binanceus, kraken")
    p.add_argument("--pairs", required=True, help="Comma symbols: BTC/USDT,ETH/USDT")
    p.add_argument("--timeframe", default="1d", help="ccxt timeframe (1d, 4h, 1h, 5m...)")
    p.add_argument("--since", default=None, help="Start date YYYY-MM-DD (optional)")
    p.add_argument("--alias-style", default="noslash",
                   choices=["noslash", "upper", "lower", "raw"],
                   help="How to map CCXT pair -> cache file symbol name")
    p.add_argument("--limit", type=int, default=1000, help="Batch size per ccxt fetch (exchange dependent)")
    p.add_argument("--max-bars", type=int, default=None, help="Stop after N bars (debug)")
    p.add_argument("--sleep-ms", type=int, default=None, help="Override ccxt rateLimit (ms)")
    return p.parse_args()


def make_exchange(exchange_id: str, rate_limit_override: int | None):
    if not hasattr(ccxt, exchange_id):
        raise SystemExit(f"Unknown exchange '{exchange_id}' in ccxt.")
    kwargs = {"enableRateLimit": True}
    if rate_limit_override is not None:
        kwargs["rateLimit"] = rate_limit_override
    ex = getattr(ccxt, exchange_id)(kwargs)
    ex.load_markets()
    return ex


def alias_for_pair(pair: str, style: str) -> str:
    if style == "raw":
        return pair
    if style == "noslash":
        return pair.replace("/", "").replace("-", "").upper()
    if style == "upper":
        return pair.upper()
    if style == "lower":
        return pair.lower()
    return pair


def timeframe_to_ms(tf: str) -> int:
    # ccxt also has parse_timeframe; we use it to be safe
    return int(ccxt.Exchange.parse_timeframe(tf) * 1000)


def parse_since(s: str | None, default_year=2017) -> int:
    if not s:
        # earliest practical default
        return int(dt.datetime(default_year, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
    d = dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp() * 1000)


def fetch_ohlcv_all(ex, pair: str, timeframe: str, since_ms: int,
                    batch_limit: int, max_bars: int | None) -> List[List]:
    """Pull all available OHLCV rows from 'since_ms' forward."""
    tf_ms = timeframe_to_ms(timeframe)
    all_rows: List[List] = []
    while True:
        batch = ex.fetch_ohlcv(pair, timeframe=timeframe, since=since_ms, limit=batch_limit)
        if not batch:
            break
        all_rows.extend(batch)
        if max_bars and len(all_rows) >= max_bars:
            break
        last_ts = batch[-1][0]
        # advance
        since_ms = last_ts + tf_ms
        if len(batch) < batch_limit:
            break
        # respect rate limit
        time.sleep(ex.rateLimit / 1000.0)
    if max_bars:
        all_rows = all_rows[:max_bars]
    return all_rows


def ohlcv_rows_to_df(rows: List[List]) -> pd.DataFrame:
    # ccxt row: [timestamp, open, high, low, close, volume]
    if not rows:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.tz_convert(None)
    df = df[["date", "open", "high", "low", "close", "volume"]].sort_values("date")
    return df


def resample_to_daily(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    # Assume bars uniform; set index & resample
    g = df.set_index("date").resample("1D", label="right", closed="right")
    daily = pd.DataFrame({
        "open": g["open"].first(),
        "high": g["high"].max(),
        "low": g["low"].min(),
        "close": g["close"].last(),
        "volume": g["volume"].sum(),
    }).dropna(subset=["open", "high", "low", "close"])
    daily = daily.reset_index()
    return daily


def read_cache(alias: str) -> pd.DataFrame | None:
    fp = CACHE_DIR / f"{alias}.parquet"
    if not fp.exists():
        return None
    return pd.read_parquet(fp)


def merge_cache(alias: str, new_df: pd.DataFrame) -> pd.DataFrame:
    old = read_cache(alias)
    if old is None or old.empty:
        return new_df
    combo = pd.concat([old, new_df], ignore_index=True)
    combo = combo.drop_duplicates(subset="date", keep="last").sort_values("date")
    return combo


def write_cache(alias: str, df: pd.DataFrame):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fp = CACHE_DIR / f"{alias}.parquet"
    df.to_parquet(fp, index=False)
    return fp


def main():
    args = parse_args()
    ex = make_exchange(args.exchange, args.sleep_ms)

    pairs = [p.strip() for p in args.pairs.split(",") if p.strip()]
    since_ms = parse_since(args.since)

    total = 0
    for pair in pairs:
        alias = alias_for_pair(pair, args.alias_style)
        print(f"[seed-ccxt] Fetching {pair} ({alias}) {args.timeframe} since {args.since or 'exchange default'}")
        rows = fetch_ohlcv_all(ex, pair, args.timeframe, since_ms, args.limit, args.max_bars)
        if not rows:
            print(f"[seed-ccxt][WARN] no data for {pair}")
            continue
        df = ohlcv_rows_to_df(rows)
        if args.timeframe != "1d":
            df = resample_to_daily(df)
        merged = merge_cache(alias, df)
        path = write_cache(alias, merged)
        print(f"[seed-ccxt] wrote {len(merged)} daily rows -> {path}")
        total += len(merged)

    print(f"[seed-ccxt] done. total rows across symbols: {total}")


if __name__ == "__main__":
    main()
