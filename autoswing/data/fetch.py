from __future__ import annotations
from pathlib import Path
from typing import Sequence
import pandas as pd

from autoswing.data.cache import merge_with_cache, write_daily_cache
from autoswing.data.sources.alpaca_source import fetch_alpaca_daily
from autoswing.data.sources.yahoo_source import fetch_yahoo_daily

def fetch_history(symbols: Sequence[str], history: str, sources: Sequence[str], project_root: Path):
    project_root = Path(project_root)
    for sym in symbols:
        df = None
        for src in sources:
            if src == "alpaca":
                df = fetch_alpaca_daily(sym, history)
            elif src == "yahoo":
                df = fetch_yahoo_daily(sym, history)
            if df is not None and not df.empty:
                break
        if df is None or df.empty:
            continue
        merged = merge_with_cache(sym, df, project_root)
        write_daily_cache(sym, merged, project_root)
