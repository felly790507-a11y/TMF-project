# src/startup.py
import json
import sys
from pathlib import Path
from datetime import datetime

# 載入 shioaji
try:
    import shioaji as sj
except Exception as e:
    print("ERROR: 無法匯入 shioaji，請確認虛擬環境已安裝 shioaji:", e)
    sys.exit(1)

CFG_PATH = Path("config/config.json")

def load_config(path=CFG_PATH):
    if not path.exists():
        raise FileNotFoundError(f"找不到設定檔: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def login_shioaji(cfg):
    simulation_mode = cfg.get("simulation", True)
    api_key = cfg.get("api_key") or cfg.get("user") or cfg.get("account")
    secret_key = cfg.get("secret_key") or cfg.get("password") or cfg.get("passwd")
    if not api_key or not secret_key:
        raise ValueError("config.json 需包含 api_key 與 secret_key（或等效欄位）")

    api = sj.Shioaji(simulation=simulation_mode)
    # 兼容不同版本 login 簽名
    try:
        api.login(api_key, secret_key)
    except TypeError:
        try:
            api.login(api_key=api_key, secret_key=secret_key)
        except TypeError:
            try:
                # 某些版本使用 person_id / passwd
                api.login(person_id=cfg.get("person_id"), passwd=secret_key)
            except Exception as e:
                raise RuntimeError(f"登入失敗，請檢查 shioaji 版本與憑證: {e}")
    except Exception as e:
        raise RuntimeError(f"登入失敗: {e}")

    print(f"✅ 登入成功｜模式：{'模擬' if simulation_mode else '真實'}")
    return api

def activate_ca_if_needed(api, cfg):
    simulation_mode = cfg.get("simulation", True)
    if not simulation_mode and cfg.get("ca_path"):
        try:
            api.activate_ca(
                ca_path=cfg.get("ca_path"),
                ca_passwd=cfg.get("ca_passwd"),
                person_id=cfg.get("person_id")
            )
            print("✅ 憑證啟用成功")
        except Exception as e:
            raise RuntimeError(f"憑證啟用失敗: {e}")

def find_contract(api, symbol):
    # 嘗試直接從 api.Contracts.Futures.<symbol> 取得
    contracts = []
    try:
        futs = getattr(api.Contracts.Futures, symbol)
        try:
            contracts = list(futs)
        except Exception:
            # 若 futs 本身就是可迭代
            try:
                for c in futs:
                    contracts.append(c)
            except Exception:
                pass
    except Exception:
        # fallback: 遍歷所有 Futures 合約
        try:
            all_futs = getattr(api.Contracts, "Futures", None) or getattr(api.Contracts, "futures", None)
            if all_futs:
                try:
                    for attr in dir(all_futs):
                        val = getattr(all_futs, attr)
                        if isinstance(val, (list, tuple)):
                            for c in val:
                                contracts.append(c)
                except Exception:
                    try:
                        for c in all_futs:
                            contracts.append(c)
                    except Exception:
                        pass
        except Exception:
            pass

    # 以 contract.code 或 contract.symbol 包含 symbol 過濾
    filtered = []
    for c in contracts:
        code = getattr(c, "code", "") or str(getattr(c, "contract_code", ""))
        sym = getattr(c, "symbol", "") or ""
        if symbol in code or symbol in sym:
            filtered.append(c)

    # 排除展期/保留代碼（常見 R1/R2）
    filtered = [c for c in filtered if not str(getattr(c, "code", "")).endswith(("R1", "R2"))]

    if not filtered:
        return None

    # 取最早交割日
    def delivery_key(c):
        d = getattr(c, "delivery_date", None)
        if isinstance(d, datetime):
            return d
        try:
            return datetime.fromisoformat(str(d))
        except Exception:
            return datetime.max

    chosen = min(filtered, key=delivery_key)
    return chosen

def subscribe_tick(api, contract):
    # 取得 QuoteType 與 QuoteVersion 的兼容方式
    QuoteType = None
    QuoteVersion = None
    try:
        from shioaji.constant import QuoteType as QT, QuoteVersion as QV
        QuoteType = QT
        QuoteVersion = QV
    except Exception:
        try:
            QuoteType = getattr(sj.constant, "QuoteType", None)
            QuoteVersion = getattr(sj.constant, "QuoteVersion", None)
        except Exception:
            QuoteType = None
            QuoteVersion = None

    if QuoteType is None or QuoteVersion is None:
        print("⚠️ 無法取得 QuoteType/QuoteVersion，請確認 shioaji 版本。跳過訂閱。")
        return

    try:
        api.quote.subscribe(contract, quote_type=QuoteType.Tick, version=QuoteVersion.v1)
        print(f"✅ 已訂閱 Tick：{getattr(contract,'code', str(contract))}")
    except Exception as e:
        print(f"⚠️ 訂閱 Tick 失敗: {e}")

def init_engines(api, contract, cfg):
    # 嘗試匯入專案內的模組，若不存在則提示並回傳 None
    try:
        from src.kline import KlineInitializer
        from src.engine import StrategyState, TickEngine
        from src.recorder import TickRecorder
        from src.logger import TradeLogger
    except Exception:
        print("⚠️ 找不到部分引擎模組 (kline/engine/recorder/logger)。請確認 src 內對應檔案存在。")
        return None

    # 初始化 kline 與指標
    kline = KlineInitializer(api=api, contract=contract, start=cfg.get("backtest", {}).get("start"), end=cfg.get("backtest", {}).get("end"))
    kline.fetch_kline()
    kline.compute_indicators()
    indicators = kline.get_indicators()

    bias = cfg.get("bias", "auto")
    state = StrategyState()
    tick_recorder = TickRecorder(filename=cfg.get("tick_record_file", "tick_record.csv"))
    trade_logger = TradeLogger(tick_recorder=tick_recorder)
    tick_engine = TickEngine(state, bias, indicators, trade_logger, tick_recorder)

    print("✅ 引擎初始化完成")
    return tick_engine

def main():
    try:
        cfg = load_config()
    except Exception as e:
        print("讀取設定失敗:", e)
        sys.exit(1)

    try:
        api = login_shioaji(cfg)
    except Exception as e:
        print("登入失敗:", e)
        sys.exit(1)

    try:
        activate_ca_if_needed(api, cfg)
    except Exception as e:
        print("憑證啟用錯誤:", e)
        sys.exit(1)

    symbol = cfg.get("contract_symbol", "TMF")
    contract = find_contract(api, symbol)
    if contract is None:
        print(f"⚠️ 找不到標的 {symbol} 的合約，請在 REPL 列出 api.Contracts 以確認結構。")
        try:
            print("Contracts summary keys:", dir(api.Contracts))
        except Exception:
            pass
        sys.exit(1)

    print(f"✅ 使用合約：{getattr(contract,'code', getattr(contract,'contract_code', str(contract)))}")

    # 初始化引擎（若有）
    engine = init_engines(api, contract, cfg)

    # 訂閱 Tick
    subscribe_tick(api, contract)

    # 若需要把 engine 與 api 綁定或註冊回調，請在此加入
    # 範例（依你專案實作調整）:
    # try:
    #     api.quote.set_callback(contract, engine.on_tick)
    # except Exception:
    #     pass

    print("啟動完成。")

if __name__ == "__main__":
    main()
