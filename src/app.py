import logging
from src.config_loader import load_config
from src.shioaji_client import ShioajiClient
from src.quote_manager import QuoteManager
from src.strategy import ThreeTickStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main_live():
    cfg = load_config()
    client = ShioajiClient(cfg)
    client.login()
    client.activate_ca_if_needed()
    contract = client.select_tmf_contract()

    strategy = ThreeTickStrategy(fee_ticks=cfg["fee_ticks"], slippage=cfg.get("slippage_ticks",0.5))
    qm = QuoteManager(on_kbar_callback=strategy.on_kbar, ticks_per_kbar=3)

    # 範例：註冊 tick handler（實際依 shioaji callback 形式調整）
    def tick_handler(exchange, tick):
        # tick 需轉成 dict: {'time':..., 'price':..., 'volume':...}
        t = {"time": tick.ts, "price": tick.close, "volume": getattr(tick, "volume", 0)}
        kbar = qm.on_tick(t)
        if kbar:
            sig = strategy.on_kbar(kbar)
            if sig:
                logger.info("Signal: %s", sig)
                # 在此下單（OCO）或模擬下單
    # 真實環境需呼叫 api.quote.subscribe 或相對應方法並綁定 tick_handler

if __name__ == "__main__":
    main_live()
