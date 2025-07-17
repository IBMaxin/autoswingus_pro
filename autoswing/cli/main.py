from __future__ import annotations

import sys
import subprocess
from pathlib import Path
import typer
from rich import print

from autoswing.utils.env import load_env
from autoswing.config.loader import load_accounts, load_settings
from autoswing.data.fetch import fetch_history
from autoswing.data.loader import load_bundle_cached
from autoswing.strategies.sma_pullback import SMAPullbackStrategy
from autoswing.backtest.backtester import run_backtest

app = typer.Typer(help="AutoSwingUS-Pro command line")
ROOT = Path(__file__).parents[2]


# ------------------------------------------------------------------ env-check
@app.command("env-check")
def env_check():
    """Validate .env + configs; warn if broker creds missing."""
    load_env(ROOT / ".env")
    accts = load_accounts(ROOT / "autoswing" / "config" / "accounts.yaml")
    missing = {}
    for name, acct in accts.items():
        if acct.broker == "alpaca":
            if not acct.key_id:
                missing.setdefault(name, []).append("key_id")
            if not acct.secret_key:
                missing.setdefault(name, []).append("secret_key")
    if not missing:
        print("[green]Environment OK.[/green]")
        raise typer.Exit()
    print("[yellow]Missing credentials:[/yellow]", missing)
    if typer.confirm("Open .env to edit now?", default=False):
        typer.launch(str(ROOT / ".env"))


# ------------------------------------------------------------------ data-fetch
@app.command("data-fetch")
def data_fetch(
    symbols: str = typer.Option(..., "--symbols", help="Comma symbols: AAPL,MSFT"),
    history: str = typer.Option("1y", "--history", help="1y,6mo,30d"),
    sources: str = typer.Option("alpaca,yahoo", "--sources", help="priority order"),
):
    load_env(ROOT / ".env")
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    srcs = [s.strip() for s in sources.split(",") if s.strip()]
    print(f"Fetching {history} for {syms} via {srcs}")
    fetch_history(syms, history, srcs, ROOT)
    print("[green]Done.[/green]")


# ------------------------------------------------------------------ paper-backtest
@app.command("paper-backtest")
def paper_backtest(days: int = typer.Option(365, "--days", help="Lookback days from cache")):
    load_env(ROOT / ".env")
    st = load_settings(ROOT / "autoswing" / "config" / "settings_default.yaml")
    bundle = load_bundle_cached(st.universe, days, ROOT)
    if not bundle:
        print("[red]No cached data. Run data-fetch or seed-ccxt first.[/red]")
        raise typer.Exit(code=1)
    strat = SMAPullbackStrategy()
    pf = run_backtest(bundle, strat, starting_cash=1000)
    print(f"Equity: {pf.equity():.2f}")


# ------------------------------------------------------------------ paper-run (alias)
@app.command("paper-run")
def paper_run():
    """Alias: paper-backtest 30d."""
    paper_backtest(days=30)


# ------------------------------------------------------------------ seed-ccxt
@app.command("seed-ccxt")
def seed_ccxt(
    exchange: str = typer.Option(..., "--exchange", help="ccxt exchange id, e.g. binanceus"),
    pairs: str = typer.Option(..., "--pairs", help="BTC/USDT,ETH/USDT"),
    timeframe: str = typer.Option("1d", "--timeframe", help="ccxt timeframe"),
    since: str = typer.Option(None, "--since", help="YYYY-MM-DD start"),
    alias_style: str = typer.Option("noslash", "--alias-style", help="noslash|upper|lower|raw"),
    limit: int = typer.Option(1000, "--limit", help="rows per batch"),
    max_bars: int = typer.Option(None, "--max-bars", help="debug"),
):
    """Seed cache from a crypto exchange via CCXT (development data)."""
    script = ROOT / "scripts" / "seed_cache_from_ccxt.py"
    if not script.exists():
        print("[red]seed_cache_from_ccxt.py missing; re-run Phase 2A seeding install.[/red]")
        raise typer.Exit(code=1)
    cmd = [
        sys.executable, str(script),
        "--exchange", exchange,
        "--pairs", pairs,
        "--timeframe", timeframe,
        "--alias-style", alias_style,
        "--limit", str(limit),
    ]
    if since:
        cmd += ["--since", since]
    if max_bars:
        cmd += ["--max-bars", str(max_bars)]
    print(f"[cyan]Running:[/cyan] {' '.join(cmd)}")
    rc = subprocess.call(cmd)
    raise typer.Exit(code=rc)

@app.command("ui")
def ui(
    port: int = typer.Option(8501, "--port", help="Streamlit port"),
    open_browser: bool = typer.Option(False, "--open-browser/--no-open-browser", help="Launch browser automatically."),
):
    """Launch the AutoSwingUS-Pro Streamlit UI."""
    script = ROOT / "autoswing" / "ui" / "app.py"
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(script),
        "--server.port", str(port),
        "--server.headless", "true",
    ]
    if not open_browser:
        # suppress usage stats to avoid outbound web calls
        cmd += ["--browser.gatherUsageStats", "false"]
    print(f"[cyan]Launching UI: {' '.join(cmd)}[/cyan]")
    subprocess.call(cmd)

def run():
    app()


if __name__ == "__main__":
    run()


from autoswing.pipeline.daily import run_pipeline
from autoswing.backtest.walkforward import walkforward
from autoswing.analysis.montecarlo import bootstrap_pnl
import pandas as pd
import json
import subprocess

@app.command("pipeline-daily")
def pipeline_daily(
    days: int = typer.Option(60, "--days", help="Lookback days for signals"),
    auto_push: bool = typer.Option(False, "--auto-push", help="Git add/push logs"),
):
    eq = run_pipeline(days=days, auto_push=auto_push)
    print(f"Final equity: {eq:.2f}")

@app.command("walkforward")
def cli_walkforward(
    symbols: str = typer.Option("", "--symbols", help="Comma symbols; blank=equities from settings"),
    train: int = typer.Option(180, "--train"),
    test: int = typer.Option(30, "--test"),
    step: int = typer.Option(30, "--step"),
):
    from autoswing.config.loader import load_settings
    ROOT = Path(__file__).parents[2]
    st = load_settings(ROOT / "autoswing" / "config" / "settings_default.yaml")
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()] or st.universe_equities
    df = walkforward(syms, train_days=train, test_days=test, step_days=step, root=ROOT)
    out = ROOT / "runtime/logs" / "walkforward_results.csv"
    df.to_csv(out, index=False)
    print(f"Saved walkforward results: {out} ({len(df)} rows)")

@app.command("montecarlo")
def cli_montecarlo(
    iters: int = typer.Option(5000, "--iters", help="Bootstrap iterations."),
    start: float = typer.Option(1000.0, "--start", help="Starting cash for simulation."),
):
    """Bootstrap Monte Carlo on recorded trade PnLs (Phase‑2B minimal)."""
    res = bootstrap_pnl(iters=iters, starting_cash=start)
    print(res)

@app.command("ui")
def cli_ui(
    port: int = typer.Option(8501, "--port", help="Streamlit port"),
    open_browser: bool = typer.Option(False, "--open-browser/--no-open-browser", help="Launch browser automatically."),
):
    ROOT = Path(__file__).parents[2]
    script = ROOT / "autoswing" / "ui" / "app.py"
    cmd = ["streamlit", "run", str(script), "--server.port", str(port)]
    if not open_browser:
        cmd += ["--server.headless", "true", "--browser.gatherUsageStats", "false"]
    subprocess.call(cmd)
