import pandas as pd
from src.utils import atr

class ThreeTickStrategy:
    """
    規則摘要：
    - 以 3-tick Kbar 為單位
    - 進場：連續 3 根同向上升/下跌 Kbar（可加成交量條件）
    - 停損：stop = max(1.2 * ATR(14), fee_ticks)
    - 目標：R:R = 1:1.8 或使用追蹤停損
    """
    def __init__(self, fee_ticks=4, slippage=0.5, tick_value=10):
        self.fee_ticks = fee_ticks
        self.slippage = slippage
        self.tick_value = tick_value
        self.kbars = []

    def on_kbar(self, kbar):
        self.kbars.append(kbar)
        if len(self.kbars) < 15:
            return None
        df = pd.DataFrame(self.kbars)
        df["atr"] = atr(df["high"], df["low"], df["close"], period=14)
        # 檢查最後 3 根是否同向上升
        last3 = df.iloc[-3:]
        up = (last3["close"].diff().fillna(0) > 0).all()
        down = (last3["close"].diff().fillna(0) < 0).all()
        if up:
            stop_ticks = max(1.2 * df["atr"].iloc[-1], self.fee_ticks)
            return {"side":"buy","price":kbar["close"], "stop_ticks":stop_ticks}
        if down:
            stop_ticks = max(1.2 * df["atr"].iloc[-1], self.fee_ticks)
            return {"side":"sell","price":kbar["close"], "stop_ticks":stop_ticks}
        return None
