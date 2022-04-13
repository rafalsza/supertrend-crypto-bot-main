import pandas_ta as ta
import vectorbt as vbt
import numpy as np
import pandas as pd
from datetime import datetime
from vectorbt.portfolio import nb
from numba import njit
from vectorbt.portfolio.enums import SizeType, Direction
from binance.client import Client

symbols = ["BTCUSDT", "ETHUSDT", "LTCUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT"]

interval = '30m'
df = vbt.BinanceData.download(symbols, start='12 months ago UTC', interval=interval).concat()

df1 = vbt.pandas_ta('ha').run(df['Open'], df['High'], df['Low'], df['Close'])
pd.set_option('display.max_columns', 30)
multiplier = np.arange(2.0, 2.6, 0.1).round(2)
length = np.arange(2, 12, 1)
st = vbt.pandas_ta('supertrend').run(df1.ha_high, df1.ha_low, df1.ha_close, length=length, multiplier=multiplier)
entries = st.supert_below(df1.ha_close)
exits = st.supert_above(df1.ha_close)
vbt.settings.portfolio['fees'] = 0.00075
vbt.settings.portfolio['sl_stop'] = 0.05
vbt.settings.portfolio['init_cash'] = 1000
vbt.settings.portfolio['freq'] = interval
vbt.settings.set_theme("dark")

portfolio1 = vbt.Portfolio.from_signals(df['Close'], entries, exits, group_by=True)
portfolio2 = vbt.Portfolio.from_signals(df['Close'], entries, exits)
cheight, cwidth = 600, 900
plot2 = portfolio2.value().vbt.plot(height=cheight, width=cwidth).show()
plot1 = portfolio1.plot_cum_returns(height=cheight, width=cwidth).show()
print(portfolio2.total_return(group_by=False))
# print(portfolio2.total_return(group_by=False).groupby('symbol').mean())
print(portfolio2.stats(group_by=True))
print(portfolio1.trades.records_readable)

benchmark = portfolio1.total_benchmark_return(group_by=False)*100
totalret = portfolio1.total_return(group_by=False)*100
total_ret = pd.DataFrame(totalret)
print(total_ret)
total_ret = total_ret.assign(benchmark_return=benchmark.values)
total_ret_des = total_ret.filter(like='SOLUSDT', axis=0)
print(total_ret_des)