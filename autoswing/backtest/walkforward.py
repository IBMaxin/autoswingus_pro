from __future__ import annotations
from pathlib import Path
from typing import Sequence, Tuple, Dict
import numpy as np
import pandas as pd
from autoswing.strategies.sma_pullback import SMAPullbackStrategy
from autoswing.backtest.backtester import run_backtest
from autoswing.data.loader import load_bundle_cached

ROOT = Path(__file__).parents[2]

def slice_windows(df: pd.DataFrame, train: int, test: int, step: int):
    n = len(df)
    idx = 0
    while idx + train + test <= n:
        yield (df.iloc[idx:idx+train], df.iloc[idx+train:idx+train+test])
        idx += step

def walkforward(symbols: Sequence[str], train_days: int, test_days: int, step_days: int, root: Path = ROOT) -> pd.DataFrame:
    """Rolling windows; train: optimize SMA lengths naive grid; test: apply fixed strat."""
    # simple grid
    fast_opts = [10,20,30]
    slow_opts = [50,100,150]
    recs = []
    bundle_full = {s: load_bundle_cached([s], 10_000, root).get(s) for s in symbols}
    for sym, df_full in bundle_full.items():
        if df_full is None or len(df_full) < slow_opts[-1]:
            continue
        for (train_df, test_df) in slice_windows(df_full.reset_index(drop=True), train_days, test_days, step_days):
            best = None
            best_pnl = -np.inf
            for f in fast_opts:
                for sl in slow_opts:
                    if sl <= f or len(train_df) < sl:
                        continue
                    sma_f = train_df.close.rolling(f).mean()
                    sma_s = train_df.close.rolling(sl).mean()
                    sig = 1 if sma_f.iloc[-1] > sma_s.iloc[-1] else 0
                    # toy pnl proxy: last close - mean(close[-5:])
                    pnl_proxy = float(train_df.close.iloc[-1] - train_df.close.tail(5).mean()) * sig
                    if pnl_proxy > best_pnl:
                        best_pnl = pnl_proxy
                        best = (f, sl)
            if best is None:
                continue
            f_best, sl_best = best
            # test window: simple result measure
            sma_f_t = test_df.close.rolling(f_best).mean()
            sma_s_t = test_df.close.rolling(sl_best).mean()
            regime = sma_f_t > sma_s_t
            ret = test_df.close.pct_change().fillna(0.0)
            pnl = float((ret * regime.shift(1).fillna(False)).add(1).prod() - 1)
            recs.append({"symbol": sym, "start": test_df.date.iloc[0], "end": test_df.date.iloc[-1],
                         "fast": f_best, "slow": sl_best, "return": pnl})
    return pd.DataFrame(recs)
