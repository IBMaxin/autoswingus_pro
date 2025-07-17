from __future__ import annotations
from pathlib import Path
import pandas as pd

CACHE_SUBDIR = "runtime/data_cache/crypto/daily"

def _cache_path(symbol: str, root: Path) -> Path:
    return Path(root) / CACHE_SUBDIR / f"{symbol.upper()}.parquet"

def ensure_cache_dir(root: Path):
    (Path(root) / CACHE_SUBDIR).mkdir(parents=True, exist_ok=True)

def read_crypto_cache(sym: str, root: Path) -> pd.DataFrame | None:
    p = _cache_path(sym, root)
    if not p.exists():
        return None
    return pd.read_parquet(p)

def write_crypto_cache(sym: str, df: pd.DataFrame, root: Path):
    ensure_cache_dir(root)
    _cache_path(sym, root).write_bytes(df.to_parquet(index=False))
