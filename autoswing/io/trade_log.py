from __future__ import annotations
import csv
from pathlib import Path
from typing import Iterable, List, Dict

HEADER = [
    "trade_id","dt","symbol","side","qty","price","notional","fee",
    "settle_dt","settled","realized_pnl","cash_after"
]

def _log_path(project_root: Path) -> Path:
    p = Path(project_root) / "runtime" / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p / "trades.csv"

def ensure_header(fp):
    if not fp.exists() or fp.stat().st_size == 0:
        with fp.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(HEADER)

def append_trades(trades: Iterable[dict], project_root):
    fp = _log_path(project_root)
    ensure_header(fp)
    with fp.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        for t in trades:
            w.writerow(t)

def read_trades(project_root) -> List[Dict]:
    fp = _log_path(project_root)
    if not fp.exists():
        return []
    with fp.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r)
