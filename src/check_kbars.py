# scripts/check_kbars.py
from src.kline import KlineInitializer
import json
from pathlib import Path

# 讀 config
cfg_path = Path("config/config.json")
if not cfg_path.exists():
    print("找不到 config/config.json，請確認檔案存在。")
    raise SystemExit(1)

cfg = json.load(open(cfg_path, "r", encoding="utf-8"))

# 建一個簡單的 KlineInitializer（不需要 api）
k = KlineInitializer(api=None, contract=None,
                     start=cfg.get("backtest", {}).get("start"),
                     end=cfg.get("backtest", {}).get("end"))

df = k.fetch_kline()

print("kbars empty:", df.empty)
print("columns:", list(df.columns))
if not df.empty:
    print(df.head(5).to_string(index=False))
else:
    print("kbars 為空，請確認 data/kbars_3tick 內是否有可讀的 CSV。")
