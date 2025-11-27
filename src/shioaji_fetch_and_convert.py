# src/shioaji_fetch_and_convert.py
import os
from pathlib import Path
import csv
import pandas as pd
import shioaji as sj

# ---------- 設定區（請修改） ----------
PERSON_ID = "YOUR_PERSON_ID"
PASSWORD = "YOUR_PASSWORD"
# 合約代碼請以你在 Shioaji 中看到的完整代碼填入，例如 "TMF202512"
CONTRACT_CODE = "TMF202512"
DATE_STR = "2025-11-26"   # YYYY-MM-DD
OUT_RAW_DIR = Path("data/raw_ticks")
OUT_KBAR_DIR = Path("data/kbars_3tick")
OUT_RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT_KBAR_DIR.mkdir(parents=True, exist_ok=True)
RAW_CSV = OUT_RAW_DIR / f"{CONTRACT_CODE}_{DATE_STR}_ticks.csv"
KBAR_CSV = OUT_KBAR_DIR / f"{CONTRACT_CODE}_{DATE_STR}_3tick.csv"
# ------------------------------------

def login_shioaji(person_id: str, password: str):
    api = sj.Shioaji()
    api.login(person_id=person_id, passwd=password)
    return api

def fetch_ticks_save(api, contract_code: str, date_str: str, out_path: Path) -> pd.DataFrame:
    print(f"抓取 {contract_code} {date_str} 的逐筆資料...")
    # 嘗試直接以代碼呼叫 ticks；若你的 shioaji 版本需要 contract 物件，請在互動式環境取得 contract 並改寫此處
    ticks = api.ticks(contract_code, date=date_str)
    rows = []
    for t in ticks:
        # 支援 dict 或物件屬性兩種情況
        time = getattr(t, "time", None) or (t.get("time") if isinstance(t, dict) else None)
        price = getattr(t, "price", None) or (t.get("price") if isinstance(t, dict) else None)
        volume = getattr(t, "volume", None) or (t.get("volume") if isinstance(t, dict) else 0)
        bid = getattr(t, "bid", None) or (t.get("bid") if isinstance(t, dict) else None)
        ask = getattr(t, "ask", None) or (t.get("ask") if isinstance(t, dict) else None)
        rows.append({"time": time, "price": price, "volume": volume, "bid": bid, "ask": ask})
    df = pd.DataFrame(rows)
    if not df.empty and not pd.api.types.is_datetime64_any_dtype(df["time"]):
        df["time"] = pd.to_datetime(df["time"])
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"已儲存原始逐筆到: {out_path} (rows: {len(df)})")
    return df

def ticks_to_3tick_kbar(df_ticks: pd.DataFrame, out_kbar_path: Path) -> pd.DataFrame:
    if df_ticks.empty:
        print("沒有逐筆資料，跳過轉檔。")
        return pd.DataFrame()
    df_ticks = df_ticks.sort_values("time").reset_index(drop=True)
    rows = []
    buffer = []
    for _, r in df_ticks.iterrows():
        buffer.append({"time": r["time"], "price": float(r["price"]), "volume": int(r.get("volume", 0))})
        if len(buffer) >= 3:
            times = [b["time"] for b in buffer[:3]]
            prices = [b["price"] for b in buffer[:3]]
            vols = [b["volume"] for b in buffer[:3]]
            kbar = {
                "time": pd.to_datetime(times[-1]).isoformat(),
                "open": prices[0],
                "high": max(prices),
                "low": min(prices),
                "close": prices[-1],
                "volume": sum(vols)
            }
            rows.append(kbar)
            buffer = buffer[3:]
    df_k = pd.DataFrame(rows)
    df_k.to_csv(out_kbar_path, index=False, encoding="utf-8")
    print(f"已儲存 3-tick Kbar 到: {out_kbar_path} (bars: {len(df_k)})")
    return df_k

def run_backtest_if_available(kbar_path: Path):
    try:
        from src.config_loader import load_config
        from src.backtest import Backtester
    except Exception:
        print("找不到 src.config_loader 或 src.backtest，跳過回測。")
        return None
    cfg = load_config()
    bt = Backtester(cfg, str(kbar_path))
    trades = bt.run()
    print("回測完成，交易筆數:", len(trades))
    out_trades = Path("backtest_trades") / f"{kbar_path.stem}.csv"
    out_trades.parent.mkdir(parents=True, exist_ok=True)
    with open(out_trades, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["side","entry","stop","target","size"])
        w.writeheader()
        for t in trades:
            w.writerow(t)
    print("交易明細已儲存:", out_trades)
    return trades

def main():
    api = login_shioaji(PERSON_ID, PASSWORD)
    df_ticks = fetch_ticks_save(api, CONTRACT_CODE, DATE_STR, RAW_CSV)
    df_kbar = ticks_to_3tick_kbar(df_ticks, KBAR_CSV)
    run_backtest_if_available(KBAR_CSV)

if __name__ == "__main__":
    main()
