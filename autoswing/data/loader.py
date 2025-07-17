from __future__ import annotations
from pathlib import Path
from typing import Sequence, Dict
import pandas as pd
from autoswing.data.cache import read_daily_cache

def load_bundle_cached(symbols: Sequence[str], days: int, project_root: Path) -> Dict[str, pd.DataFrame]:
    project_root = Path(project_root)
    out = {}
    for sym in symbols:
        df = read_daily_cache(sym, project_root)
        if df is None or df.empty:
            continue
        out[sym] = df.tail(days).reset_index(drop=True)
    return out
