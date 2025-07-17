"""
AutoSwingUS-Pro Streamlit UI (Phase UI-A patched).
- Status page: shows cash, positions, last pipeline run.
- Backtest page: pick symbols, lookback, run SMA Pullback over cached data.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st

from autoswing.utils.env import load_env
from autoswing.config.loader import load_settings
from autoswing.data.loader import load_bundle_cached
from autoswing.backtest.backtester import run_backtest
from autoswing.strategies.sma_pullback import SMAPullbackStrategy
from autoswing.engine.portfolio import Portfolio

PROJECT_ROOT = Path(__file__).parents[2]
STATUS_DIR = PROJECT_ROOT / "runtime" / "status"
STATUS_DIR.mkdir(parents=True, exist_ok=True)
STATUS_FILE = STATUS_DIR / "last_pipeline.json"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _load_last_status():
    if STATUS_FILE.exists():
        try:
            return json.loads(STATUS_FILE.read_text())
        except Exception:
            pass
    return {"msg": "no pipeline run yet"}


def _discover_cached_symbols() -> List[str]:
    cache_dir = PROJECT_ROOT / "runtime" / "data_cache" / "daily"
    return sorted([p.stem for p in cache_dir.glob("*.parquet")])


def _bundle_to_normalized_df(bundle: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Take {symbol: df} and return a dataframe of normalized closes (start=1),
    outer-joined on date. Skips symbols w/ fewer than 2 rows.
    """
    series_list = []
    for sym, df in bundle.items():
        if df is None or df.empty or "close" not in df or len(df) < 2:
            continue
        s = pd.Series(df["close"].values, index=pd.to_datetime(df["date"]), name=sym)
        s = s / s.iloc[0]  # normalize start=1
        series_list.append(s)
    if not series_list:
        return pd.DataFrame()
    out = pd.concat(series_list, axis=1, join="outer").sort_index()
    return out


# ------------------------------------------------------------------
# Sidebar nav
# ------------------------------------------------------------------
def sidebar_nav() -> str:
    st.sidebar.title("AutoSwingUS-Pro")
    choice = st.sidebar.radio("Sections", ["Status", "Backtest"])
    return choice


# ------------------------------------------------------------------
# Pages
# ------------------------------------------------------------------
def page_status():
    st.header("System Status")
    stat = _load_last_status()
    st.json(stat)
    st.markdown("### Quick Actions")
    st.write("Use the terminal to run:")
    st.code("autoswingctl pipeline-daily\nautoswingctl data-fetch --symbols AAPL,MSFT --history 3y")


def page_backtest():
    st.header("Quick Backtest")

    # load settings for default universe
    load_env(PROJECT_ROOT / ".env")
    settings = load_settings(PROJECT_ROOT / "autoswing" / "config" / "settings_default.yaml")
    default_syms = settings.universe or []

    cached = _discover_cached_symbols()
    if not cached:
        st.warning("No cached data found. Run a data fetch in the terminal first.")
        return

    symbols = st.multiselect(
        "Symbols",
        cached,
        default=[s for s in default_syms if s in cached][:5] or cached[:5],
    )
    lookback_days = st.slider("Lookback (days)", min_value=30, max_value=2000, value=365, step=5)

    run_it = st.button("Run Backtest", type="primary")
    if not run_it:
        return

    # ---- load data
    bundle = load_bundle_cached(symbols, lookback_days, PROJECT_ROOT)
    if not bundle:
        st.error("No data loaded.")
        return

    # ---- run strategy backtest
    strat = SMAPullbackStrategy()
    pf = run_backtest(bundle, strat, starting_cash=1000.0)
    final_eq = pf.equity()
    st.success(f"Backtest complete. Final equity: **${final_eq:,.2f}**")

    # ---- build normalized symbol chart
    norm_df = _bundle_to_normalized_df(bundle)
    if not norm_df.empty:
        st.markdown("#### Price (normalized start=1)")
        st.line_chart(norm_df)

    # ---- placeholder portfolio curve (Phase UI-B: real equity curve)
    # For now we just show a 2-point line from start->final to give visual feedback.
    pf_curve = pd.Series(
        data=[1000.0, final_eq],
        index=pd.to_datetime(["2000-01-01", "2000-01-02"]),
        name="Portfolio",
    )
    st.markdown("#### Portfolio (placeholder)")
    st.line_chart(pf_curve.to_frame())

    # ---- Show underlying data (collapsible)
    with st.expander("Show raw data (tail)"):
        for sym, df in bundle.items():
            st.write(sym)
            st.dataframe(df.tail())


# ------------------------------------------------------------------
def main():
    page = sidebar_nav()
    if page == "Status":
        page_status()
    elif page == "Backtest":
        page_backtest()


if __name__ == "__main__":
    st.set_page_config(page_title="AutoSwingUS-Pro", layout="wide")
    main()
