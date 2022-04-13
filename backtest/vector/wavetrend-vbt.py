import pandas as pd
import vectorbt as vbt
import numpy as np


def wavetrend(high, low, close, n1, n2):
    ap = (high + low + close) / 3.0  # HLC3
    ap = pd.DataFrame(ap)
    esa = ap.ewm(span=n1, adjust=False).mean()  # EMA
    d = (abs(ap - esa)).ewm(span=n1, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d)
    wt1 = ci.ewm(span=n2, adjust=False).mean()
    wt2 = wt1.rolling(4).mean()
    return wt1, wt2


Wavetrend = vbt.IndicatorFactory(
    class_name='Wavetrend',
    short_name='wt',
    input_names=['high', 'low', 'close'],
    param_names=['n1', 'n2'],
    output_names=['wt1', 'wt2'], ).from_apply_func(wavetrend)

symbols = ['BTCUSDT', 'LTCUSDT', 'XRPUSDT', 'LUNAUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT']

interval = '1h'
df = vbt.BinanceData.download(symbols, start='12 months ago UTC', interval=interval).concat()


obLevel1 = 60
obLevel2 = 53
obLevel3 = 100
osLevel1 = -60
osLevel2 = -53
osLevel3 = -75

best_parameters = []
n11 = range(10, 40, 1)
n22 = range(10, 40, 1)
sl_losses = [0.04, 0.06, 0.08, 0.1]

for n1 in n11:
    for n2 in n22:
        for sl in sl_losses:
            wt = Wavetrend.run(df['High'], df['Low'], df['Close'], n1=n1, n2=n2)
            entries = wt.wt1_crossed_below(osLevel1)
            exits = wt.wt1_crossed_above(obLevel1)
            pf = vbt.Portfolio.from_signals(
                sl_stop=sl,
                fees=0.00075,
                freq=interval,
                init_cash=1000,
                close=df['Close'],
                entries=entries,
                exits=exits,
            )
            stats = pf.stats(column=(n1, n2, 'BTCUSDT'))
            if stats['Profit Factor'] > 1.5:
                print(f'n1: {n1}, n2: {n2}, sl: {sl}, return: {stats["Total Return [%]"]}')
                best_parameters.append({
                    'n1': n1,
                    'n2': n2,
                    'sl': sl,
                    'stat': stats
                })

# entries = wt.wt1_crossed_below(osLevel1) & cmo.cmo_crossed_below(osLevel1)
# exits = wt.wt1_crossed_above(obLevel1) & cmo.cmo_crossed_above(obLevel1)
