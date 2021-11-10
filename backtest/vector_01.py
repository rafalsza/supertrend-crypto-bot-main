import pandas as pd
import numpy as np
import pandas_ta as ta
import vectorbt as vbt
import logging

pd.set_option('display.max_columns', 30)
symbols = [
    'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'LTCUSDT',
    'BNBUSDT', 'ADAUSDT'
]

coin = 'BNB'
symbol = coin + 'USDT'
multiplier = 2.0
length = 3
cols = ['Open', 'High', 'Low', 'Close', 'Volume']
# data = vbt.BinanceData.download(symbol, start='9 months ago UTC', interval='30m')
df = vbt.BinanceData.download(symbol, start='3 months ago UTC', interval='30m').get(cols)
# open = data.get('Open')
# high = data.get('High')
# low = data.get('Low')
# close = data.get('Close')
normal_candle = df['Close']
volume = df['Volume']

# HEIKIN_ASHI
df = ta.ha(df['Open'], df['High'], df['Low'], df['Close'])
df = pd.concat([df, volume, normal_candle], axis=1)

# open_h = ta.ha(open, high, low, close)['HA_open']
# high_h = ta.ha(open, high, low, close)['HA_high']
# low_h = ta.ha(open, high, low, close)['HA_low']
# close_h = ta.ha(open, high, low, close)['HA_close']

# st = ta.supertrend(high_h, low_h, close_h, length=length, multiplier=multiplier)[
#     f'SUPERT_{length}_{multiplier}']
st = ta.supertrend(high=df['HA_high'], low=df['HA_low'], close=df['HA_close'], length=length, multiplier=multiplier)[
    f'SUPERT_{length}_{multiplier}']
exits = ta.cross_value(st, df.HA_close)
entries = ta.cross_value(st, df.HA_close, above=False)
vbt.settings.portfolio['freq'] = '30m'
vbt.settings.portfolio['fees'] = 0.00075
vbt.settings.portfolio['sl_stop'] = 0.05
vbt.settings.portfolio['init_cash'] = 1000
portfolio = vbt.Portfolio.from_signals(normal_candle, entries, exits, size=1)

plot1 = portfolio.plot().show()
print(portfolio.stats())
# print(portfolio.trades.records)
# print(portfolio.trades.records_readable)
plot2 = portfolio.trades.plot().show()
portfolio.save('my_pf')
