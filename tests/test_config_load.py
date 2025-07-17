from pathlib import Path
from autoswing.config.loader import load_accounts, load_settings

ROOT = Path(__file__).parents[1]

def test_load_accounts():
    p = ROOT / 'autoswing' / 'config' / 'accounts.yaml'
    accts = load_accounts(p)
    assert 'alpaca_paper' in accts
    assert accts['alpaca_paper'].starting_cash == 1000

def test_load_settings():
    p = ROOT / 'autoswing' / 'config' / 'settings_default.yaml'
    st = load_settings(p)
    assert st.timeframe == '1d'
    assert st.max_positions == 5
