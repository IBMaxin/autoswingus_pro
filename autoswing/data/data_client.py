"""Unified data access layer (Phase 1: CSV only)."""
from __future__ import annotations
import os
import pandas as pd
from pathlib import Path


class LocalCSVDataClient:
    """Loads OHLCV daily bars from CSV files under a root directory.
    Expected filename pattern: <symbol>.csv with columns: date,open,high,low,close,volume.
    """

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def available(self):
        return [p.stem.upper() for p in self.root.glob("*.csv")]

    def load(self, symbol: str) -> pd.DataFrame:
        fp = self.root / f"{symbol.upper()}.csv"
        if not fp.exists():
            raise FileNotFoundError(fp)
        df = pd.read_csv(fp, parse_dates=["date"])
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
