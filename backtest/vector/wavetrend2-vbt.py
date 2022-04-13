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
    input_names=['high', 'low', 'close'],
    param_names=['n1', 'n2'],
    output_names=['wt1', 'wt2'], ).from_apply_func(wavetrend)

symbols = ['BTCUSDT', 'LTCUSDT', 'LUNAUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT']

interval = '4h'
df = vbt.BinanceData.download(symbols, start='12 months ago UTC', interval=interval).concat()

obLevel1 = 60
obLevel2 = 53
osLevel1 = -60
osLevel2 = -53

best_parameters = []
n11 = [10, 22]
n22 = [21, 22]
sl_losses = [0.04, 0.06, 0.08, 0.1]
trail = [0.01, 0.03, 0.05, 0.07, 0.1,0.2]
tp_profits = [0.02, 0.04, 0.06, 0.08, 0.1, 0.15]
for n1 in n11:
    for n2 in n22:
        for sl in sl_losses:
            for tr in trail:
                for tp in tp_profits:
                    wt = Wavetrend.run(df['High'], df['Low'], df['Close'], n1=n1, n2=n2)
                    cmo = vbt.pandas_ta('cmo').run(df['Close'], lenght=14, talin=False)
                    entries3 = wt.wt1_crossed_below(osLevel1) & cmo.cmo_crossed_below(osLevel1)
                    pf = vbt.Portfolio.from_signals(
                        sl_stop=sl,
                        tp_stop=tp,
                        sl_trail=tr,
                        fees=0.00075,
                        freq=interval,
                        init_cash=1000,
                        close=df['Close'],
                        entries=entries3,
                    )
                    stats = pf.stats(column=(n1, n2, 'ADAUSDT'))
                    if stats['Profit Factor'] > 1.5:
                        print(f'n1: {n1}, n2: {n2}, sl: {sl}, tp: {tp}, tr: {tr}, return: {stats["Total Return [%]"]}')
                        best_parameters.append({
                            'n1': n1,
                            'n2': n2,
                            'sl': sl,
                            'tr': tr,
                            'tp': tp,
                            'stat': stats
                        })
