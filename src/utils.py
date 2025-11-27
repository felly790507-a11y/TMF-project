import pandas as pd
import numpy as np

def atr(series_high, series_low, series_close, period=14):
    high = pd.Series(series_high)
    low = pd.Series(series_low)
    close = pd.Series(series_close)
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period, min_periods=1).mean()
    return atr

def calc_position_size(capital, risk_pct, stop_ticks, tick_value=10):
    risk_amount = capital * (risk_pct / 100.0)
    per_contract_risk = stop_ticks * tick_value
    if per_contract_risk <= 0:
        return 0
    size = int(risk_amount // per_contract_risk)
    return max(1, size) if size >= 1 else 0
