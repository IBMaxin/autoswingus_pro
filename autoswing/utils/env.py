from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

_loaded = False

def load_env(dotenv_path=None):
    """Load environment variables from .env exactly once."""
    global _loaded
    if _loaded:
        return
    if dotenv_path is None:
        dotenv_path = Path.cwd() / ".env"
    else:
        dotenv_path = Path(dotenv_path)
    load_dotenv(dotenv_path=dotenv_path, override=False)
    _loaded = True
