from pathlib import Path
import pandas as pd
from autoswing.data.cache import write_daily_cache, read_daily_cache, merge_with_cache

def test_cache_roundtrip(tmp_path):
    df = pd.DataFrame({"date": pd.date_range("2025-01-01", periods=3),
                       "open":[1,2,3],"high":[1,2,3],"low":[1,2,3],"close":[1,2,3],"volume":[100,100,100]})
    proj = tmp_path / "proj"; proj.mkdir()
    (proj / "runtime/data_cache/daily").mkdir(parents=True)
    write_daily_cache("TEST", df, proj)
    rd = read_daily_cache("TEST", proj)
    assert rd is not None and len(rd)==3

def test_merge_dedup(tmp_path):
    proj = tmp_path / "proj"; proj.mkdir()
    (proj / "runtime/data_cache/daily").mkdir(parents=True)
    df1 = pd.DataFrame({"date": pd.date_range("2025-01-01", periods=2),
                        "open":[1,2],"high":[1,2],"low":[1,2],"close":[1,2],"volume":[10,20]})
    df2 = pd.DataFrame({"date": pd.date_range("2025-01-02", periods=2),
                        "open":[2,3],"high":[2,3],"low":[2,3],"close":[2,3],"volume":[20,30]})
    write_daily_cache("TEST", df1, proj)
    merged = merge_with_cache("TEST", df2, proj)
    assert len(merged)==3
