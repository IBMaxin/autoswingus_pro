"""Configuration loading utilities (env‑aware)."""
from __future__ import annotations
import os
import yaml
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class AccountConfig(BaseModel):
    broker: str
    type: str  # 'cash' or 'margin'
    key_id: Optional[str] = None
    secret_key: Optional[str] = None
    base_url: Optional[str] = None
    data_source: Optional[str] = None
    starting_cash: float = 0.0
    active: bool = True  # auto‑disabled if creds missing


class Settings(BaseModel):
    timeframe: str = "1d"
    run_schedule: str = "after_close"
    universe: List[str] = Field(default_factory=list)
    risk_per_trade: float = 0.02
    max_positions: int = 5
    enforce_cash_settlement: bool = True
    warn_pdt_trades: bool = True
    default_order_type: str = "limit"


def _expand_env(val: str):
    if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
        return os.getenv(val[2:-1], "")
    return val


def _expand_mapping(d: dict) -> dict:
    return {k: _expand_env(v) for k, v in d.items()}


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_accounts(path: str) -> Dict[str, AccountConfig]:
    raw = load_yaml(path)
    accounts_raw = raw.get("accounts", {})
    accounts: Dict[str, AccountConfig] = {}
    for name, cfg in accounts_raw.items():
        cfg = _expand_mapping(cfg)
        acct = AccountConfig(**cfg)
        # auto‑disable alpaca acct if missing key/secret
        if acct.broker == "alpaca" and (not acct.key_id or not acct.secret_key):
            acct.active = False
        accounts[name] = acct
    return accounts


def load_settings(path: str) -> Settings:
    raw = load_yaml(path)
    return Settings(**raw)
