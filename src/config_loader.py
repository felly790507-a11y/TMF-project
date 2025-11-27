import json
from pathlib import Path

def load_config(path="config/config.json"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with p.open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    # minimal validation
    required = ["simulation","api_key","secret_key","contract_symbol","fee_ticks"]
    for k in required:
        if k not in cfg:
            raise KeyError(f"Missing config key: {k}")
    return cfg
