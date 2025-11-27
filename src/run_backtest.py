from src.config_loader import load_config
from src.backtest import Backtester
import csv

cfg = load_config()
bt = Backtester(cfg, 'data/kbars_3tick/sample.csv')
trades = bt.run()
print('trades:', len(trades))

with open('backtest_trades.csv','w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['side','entry','stop','target','size'])
    w.writeheader()
    for t in trades:
        w.writerow(t)
print('saved backtest_trades.csv')
