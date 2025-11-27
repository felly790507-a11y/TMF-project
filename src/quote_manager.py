from collections import deque
import pandas as pd

class QuoteManager:
    """
    將 tick 聚合為 3-tick Kbar。
    使用簡單緩衝：每收到一筆 tick（價格、volume），累積到 3 筆後輸出一根 Kbar。
    提供 callback 機制讓 strategy 接收 kbar。
    """
    def __init__(self, on_kbar_callback=None, ticks_per_kbar=3):
        self.ticks_per_kbar = ticks_per_kbar
        self.buffer = deque()
        self.on_kbar = on_kbar_callback

    def on_tick(self, tick):
        """
        tick: dict-like with keys: 'time','price','volume'
        """
        self.buffer.append(tick)
        if len(self.buffer) >= self.ticks_per_kbar:
            k = self._build_kbar(list(self.buffer)[:self.ticks_per_kbar])
            for _ in range(self.ticks_per_kbar):
                self.buffer.popleft()
            if self.on_kbar:
                self.on_kbar(k)
            return k
        return None

    def _build_kbar(self, ticks):
        times = [t["time"] for t in ticks]
        prices = [t["price"] for t in ticks]
        vols = [t.get("volume", 0) for t in ticks]
        kbar = {
            "time": times[-1],
            "open": prices[0],
            "high": max(prices),
            "low": min(prices),
            "close": prices[-1],
            "volume": sum(vols)
        }
        return kbar
