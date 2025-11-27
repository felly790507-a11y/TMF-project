# src/engine.py
class StrategyState:
    def __init__(self):
        self.position = 0
        self.last_tick = None

class TickEngine:
    def __init__(self, state: StrategyState, bias: str, indicators: dict, trade_logger=None, tick_recorder=None):
        self.state = state
        self.bias = bias
        self.indicators = indicators
        self.trade_logger = trade_logger
        self.tick_recorder = tick_recorder

    def on_tick(self, tick: dict):
        self.state.last_tick = tick
        if self.tick_recorder:
            try:
                self.tick_recorder.record(tick)
            except Exception:
                pass

    def on_order_filled(self, order: dict):
        if self.trade_logger:
            self.trade_logger.log_trade(order)
