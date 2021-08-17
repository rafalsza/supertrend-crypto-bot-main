import pandas_ta as ta
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import warnings
from datetime import datetime
from binance import Client
import mplfinance as mpf

warnings.filterwarnings('ignore')
plt.style.use('fivethirtyeight')
plt.rcParams['figure.figsize'] = (20, 10)
# client = Client(config.BINANCE_API_KEY2, config.BINANCE_SECRET_KEY2)
client = Client("", "")
coin = 'LTC'
symbol = coin+'USDT'
length = 3
multiplier = 2.7
interval = '1h'
start_str = '6 months ago UTC'
end_str = f'{datetime.now()}'


def run_bot():
    print(f"Fetching new bars for {datetime.now().isoformat()}")
    candlesticks = client.get_historical_klines(symbol, interval, start_str, end_str)
    # trim each candle
    for candle in candlesticks:
        del candle[-6:]  # only need the first few columns
    df = pd.DataFrame(candlesticks[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']).astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index(pd.DatetimeIndex(df['timestamp'].values))
    df = ta.ha(df['open'], df['high'], df['low'], df['close'])
    df = round(df, 4)
    supertrend = round(
        df.ta.supertrend(high=df['HA_high'], low=df['HA_low'], close=df['HA_close'], length=length, multiplier=multiplier), 4)
    # df['percent'] = (ta.percent_return(df['HA_close'], cumulative=True, append=True)) * 100
    # df['percent'] = round(df['percent'], 2)
    df = pd.concat([df, supertrend], axis=1)

    # print(df)
    # ta.sma(df['HA_close'], length=10)
    # ta.ema(df['HA_close'], length=1)
    # supertrend = df.ta.supertrend(high=df['HA_high'], low=df['HA_low'], close=df['HA_close'], lenght=12,
    # multiplier=2.1)['SUPERT_7_2.1']
    # df = pd.concat([df, supertrend], axis = 1)

    # supertrend = df.ta.supertrend(high=df['HA_high'], low=df['HA_low'], close=df['HA_close'], length=12, multiplier=9.0)

    # df = df.drop(index=df.index[[0, 1, 2, 3, 4, 5, 6, 7]])

    # balance = exchange.fetch_balance()
    # print('---BNB------')
    # print(balance['free']['BNB'])
    # print('----USDT----')
    # print(balance['free']['USDT'])
    # Calculate Returns and append to the df DataFrame

    # df['percent'] = ta.percent_return(df['HA_close'], cumulative=True, append=True)

    # df = pd.concat([df, supertrend], axis=1)
    # print(df.tail(50))

    # SUPERTREND STRATEGY

    def implement_st_strategy(prices, st):
        buy_price = []
        sell_price = []
        st_signal = []
        signal = 0

        for i in range(len(st)):
            if st[i - 1] > prices[i - 1] and st[i] < prices[i]:
                if signal != 1:
                    buy_price.append(prices[i])
                    sell_price.append(np.nan)
                    signal = 1
                    st_signal.append(signal)
                else:
                    buy_price.append(np.nan)
                    sell_price.append(np.nan)
                    st_signal.append(0)
            elif st[i - 1] < prices[i - 1] and st[i] > prices[i]:
                if signal != -1:
                    buy_price.append(np.nan)
                    sell_price.append(prices[i])
                    signal = -1
                    st_signal.append(signal)
                else:
                    buy_price.append(np.nan)
                    sell_price.append(np.nan)
                    st_signal.append(0)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                st_signal.append(0)

        return buy_price, sell_price, st_signal

    buy_price, sell_price, st_signal = implement_st_strategy(df['HA_close'], df[f'SUPERT_{length}_{multiplier}'])

    # SUPERTREND SIGNALS
    plt.plot(df['HA_close'], linewidth=2)
    plt.plot(df[f'SUPERTl_{length}_{multiplier}'], color='green', linewidth=2, label='ST UPTREND')
    plt.plot(df[f'SUPERTs_{length}_{multiplier}'], color='r', linewidth=2, label='ST DOWNTREND')
    plt.plot(df.index, buy_price, marker='^', color='green', markersize=12, linewidth=0, label='BUY SIGNAL')
    plt.plot(df.index, sell_price, marker='v', color='r', markersize=12, linewidth=0, label='SELL SIGNAL')
    plt.title(f'{symbol} ST TRADING SIGNALS')
    plt.legend(loc='upper left')
    plt.show()


run_bot()
