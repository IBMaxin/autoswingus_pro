from __future__ import annotations
from pathlib import Path
import pandas as pd

CACHE_SUBDIR = Path("runtime/data_cache/daily")

def _cache_path(symbol: str, project_root: Path) -> Path:
    return project_root / CACHE_SUBDIR / f"{symbol.upper()}.parquet"

def ensure_cache_dir(project_root: Path):
    (project_root / CACHE_SUBDIR).mkdir(parents=True, exist_ok=True)

def read_daily_cache(symbol: str, project_root: Path) -> pd.DataFrame | None:
    fp = _cache_path(symbol, project_root)
    if not fp.exists():
        return None
    return pd.read_parquet(fp)

def write_daily_cache(symbol: str, df: pd.DataFrame, project_root: Path):
    ensure_cache_dir(project_root)
    fp = _cache_path(symbol, project_root)
    df.to_parquet(fp, index=False)

def merge_with_cache(symbol: str, newdf: pd.DataFrame, project_root: Path) -> pd.DataFrame:
    old = read_daily_cache(symbol, project_root)
    if old is None or old.empty:
        return newdf.sort_values("date")
    combo = pd.concat([old, newdf], ignore_index=True)
    combo = combo.drop_duplicates(subset="date", keep="last").sort_values("date")
    return combo
