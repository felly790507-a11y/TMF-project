# src/logger.py
from typing import Any

class TradeLogger:
    def __init__(self, tick_recorder=None):
        self.tick_recorder = tick_recorder

    def log_trade(self, trade: dict):
        print('TRADE:', trade)
        if self.tick_recorder:
            try:
                self.tick_recorder.record(trade)
            except Exception:
                pass

    def info(self, *args: Any):
        print('[INFO]', *args)

    def error(self, *args: Any):
        print('[ERROR]', *args)
