import numpy as np
import math
import vectorbt as vbt
import pandas_ta as ta
import pandas as pd


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
    input_names=['high', 'low', 'close'],
    param_names=['n1', 'n2'],
    output_names=['wt1', 'wt2'], ).from_apply_func(wavetrend)

symbols = ['BTCUSDT', 'LTCUSDT', 'XRPUSDT', 'LUNAUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT']
start = '12 months ago UTC'
interval = '1h'
df = vbt.BinanceData.download(symbols, start=start, interval=interval).concat()

obLevel1 = 60
obLevel2 = 53
obLevel3 = 100
osLevel1 = -60
osLevel2 = -53
osLevel3 = -75


def optimize(params):
    n1, n2, sl_stop = params
    wt = Wavetrend.run(df['High'], df['Low'], df['Close'], n1=n1, n2=n2)
    entries = wt.wt1_crossed_below(osLevel1)
    exits = wt.wt1_crossed_above(obLevel1)

    pf = vbt.Portfolio.from_signals(close=df['Close'], entries=entries, exits=exits,
                                    init_cash=100, fees=0.00075, sl_stop=sl_stop, freq=interval,
                                    direction="longonly")
    return pf.total_profit()


def optimize_all(params):
    res = optimize(params)
    return sum(res) * -1


from hyperopt import fmin, tpe, hp

best = fmin(optimize_all,
            space=[hp.uniform('n1', 10, 40), hp.uniform('n2', 10, 40),
                   hp.uniform('sl_stop', 0.01, 0.1)],
            algo=tpe.suggest,
            max_evals=100)

print(best)
