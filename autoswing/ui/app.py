from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from autoswing.pipeline.daily import run_pipeline
from autoswing.config.loader import load_settings
from autoswing.backtest.walkforward import walkforward
from autoswing.analysis.montecarlo import load_trade_returns, mc_paths

ROOT = Path(__file__).parents[2]
LOGDIR = ROOT / "runtime/logs"

st.set_page_config(page_title="AutoSwingUS-Pro", layout="wide")
st.sidebar.title("AutoSwingUS-Pro")
page = st.sidebar.radio("Sections", ["Status","Backtest","Pipeline","Walk-Forward","Monte Carlo"])

def _load_equity_curve():
    f = LOGDIR / "equity_curve.csv"
    if not f.exists():
        return pd.DataFrame(columns=["date","equity"])
    return pd.read_csv(f, parse_dates=["date"])

if page == "Status":
    st.header("System Status")
    ec = _load_equity_curve()
    if ec.empty:
        st.code('{"msg":"no pipeline run yet"}')
    else:
        st.line_chart(ec.set_index("date")["equity"])
    st.subheader("Quick Actions")
    st.code("autoswingctl pipeline-daily\nautoswingctl data-fetch --symbols AAPL,MSFT --history 3y")

elif page == "Backtest":
    st.header("Backtest (cached)")
    days = st.number_input("Lookback days", 30, 2000, 365, step=5)
    if st.button("Run Backtest"):
        from autoswing.cli.main import paper_backtest
        paper_backtest(days=days)

elif page == "Pipeline":
    st.header("Daily Pipeline Run")
    days = st.number_input("Signal lookback days", 10, 250, 60, step=5, key="pipe_days")
    push = st.checkbox("Git auto-push logs", value=False)
    if st.button("Run Pipeline Now"):
        eq = run_pipeline(days=days, auto_push=push)
        st.success(f"Pipeline complete. Final equity: {eq:.2f}")
        ec = _load_equity_curve()
        if not ec.empty:
            st.line_chart(ec.set_index("date")["equity"])

elif page == "Walk-Forward":
    st.header("Walk-Forward Analysis")
    st.caption("Rolling train/test optimization demo.")
    st.write("Defaults: 180 train / 30 test / 30 step.")
    st.write("Symbols from settings.")
    if st.button("Run Walk-Forward"):
        st.write("Running...")
        st.experimental_rerun()
    # detect rerun trigger by checking new results file
    wf_file = LOGDIR / "walkforward_results.csv"
    if wf_file.exists():
        df = pd.read_csv(wf_file, parse_dates=["start","end"])
        st.dataframe(df)
        st.bar_chart(df.groupby("symbol")["return"].mean())

elif page == "Monte Carlo":
    st.header("Monte Carlo Simulation")
    iters = st.slider("Iterations", 1000, 20000, 10000, step=1000)
    if st.button("Run MC from trade logs"):
        arr = load_trade_returns("trades")
        res = mc_paths(arr, iters=iters, start_equity=1000.0)
        st.json(res)
        st.write("Distribution of finals:")
        st.bar_chart(pd.DataFrame(res["final_samples"], columns=["final"]))
