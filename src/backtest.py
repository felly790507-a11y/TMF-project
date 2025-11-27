import pandas as pd
from src.strategy import ThreeTickStrategy
from src.utils import calc_position_size

class Backtester:
    def __init__(self, config, kbar_csv_path):
        self.config = config
        self.kbars = pd.read_csv(kbar_csv_path, parse_dates=["time"])
        self.strategy = ThreeTickStrategy(fee_ticks=config["fee_ticks"],
                                          slippage=config.get("slippage_ticks",0.5))
        self.capital = config["backtest"]["initial_capital"]
        self.risk_pct = config["backtest"].get("risk_per_trade_pct", 0.5)
        self.tick_value = 10

    def run(self):
        trades = []
        for _, row in self.kbars.iterrows():
            kbar = row.to_dict()
            signal = self.strategy.on_kbar(kbar)
            if signal:
                stop = signal["stop_ticks"]
                size = calc_position_size(self.capital, self.risk_pct, stop, tick_value=self.tick_value)
                if size <= 0:
                    continue
                entry = signal["price"] + (self.strategy.slippage if signal["side"]=="buy" else -self.strategy.slippage)
                target = entry + (1.8 * stop if signal["side"]=="buy" else -1.8 * stop)
                # 簡化：假設達到 target 或 stop 以 kbar.close 判斷
                trades.append({
                    "side": signal["side"],
                    "entry": entry,
                    "stop": entry - stop if signal["side"]=="buy" else entry + stop,
                    "target": target,
                    "size": size
                })
        return trades
