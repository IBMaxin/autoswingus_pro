from pathlib import Path
from autoswing.data.data_client import LocalCSVDataClient
from autoswing.strategies.sma_pullback import SMAPullbackStrategy
from autoswing.backtest.backtester import run_backtest

ROOT = Path(__file__).parents[1]

def test_backtest_runs():
    data_dir = ROOT / 'autoswing' / 'data'
    dc = LocalCSVDataClient(data_dir)
    syms = dc.available()
    assert syms, "no CSV data found"
    bundle = {s: dc.load(s) for s in syms}
    strat = SMAPullbackStrategy()
    pf = run_backtest(bundle, strat, starting_cash=1000)
    eq = pf.equity()
    assert isinstance(eq, float)
    assert eq <= 1000  # mark-to-cost in Phase 1
