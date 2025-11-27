# src/kline.py
from typing import Optional, Dict, Any
from pathlib import Path
import pandas as pd
from datetime import datetime

class KlineInitializer:
    def __init__(self, api=None, contract=None, start: Optional[str]=None, end: Optional[str]=None):
        self.api = api
        self.contract = contract
        self.start = start
        self.end = end
        self.kbars = pd.DataFrame()
        self.indicators: Dict[str, Any] = {}

    def fetch_kline(self):
        # 優先嘗試用 api 抓取，否則從 data/kbars_3tick 讀檔
        if self.api is not None and self.contract is not None:
            try:
                if hasattr(self.api, 'kbars'):
                    df = self.api.kbars(self.contract, start=self.start, end=self.end)
                    if not isinstance(df, pd.DataFrame):
                        df = pd.DataFrame(df)
                    self.kbars = df
                    return self.kbars
            except Exception:
                pass
        data_dir = Path('data/kbars_3tick')
        for p in data_dir.glob('*.csv'):
            try:
                df = pd.read_csv(p, parse_dates=['time'])
                self.kbars = df
                return self.kbars
            except Exception:
                continue
        self.kbars = pd.DataFrame()
        return self.kbars

    def compute_indicators(self, atr_period: int = 14):
        if self.kbars.empty:
            self.indicators = {}
            return self.indicators
        df = self.kbars.copy()
        for col in ['high','low','close']:
            if col not in df.columns:
                raise ValueError(f'missing column {col}')
        high = df['high'].astype(float)
        low = df['low'].astype(float)
        close = df['close'].astype(float)
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1,tr2,tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=atr_period, min_periods=1).mean()
        df['atr'] = atr
        self.kbars = df
        self.indicators = {'atr_period': atr_period, 'atr': atr}
        return self.indicators

    def get_indicators(self):
        if not self.indicators and not self.kbars.empty:
            self.compute_indicators()
        last_atr = None
        if 'atr' in self.indicators:
            last_atr = self.indicators['atr'].iloc[-1] if len(self.indicators['atr'])>0 else None
        elif 'atr' in self.kbars.columns:
            last_atr = self.kbars['atr'].iloc[-1] if not self.kbars.empty else None
        return {'last_atr': float(last_atr) if last_atr is not None else None, 'kbars': self.kbars}
