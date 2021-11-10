from binance.client import Client
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import time
from datetime import datetime
import pandas_ta as pta
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression
import os, sys

client = Client("", "")


class Trader:
    def __init__(self, file):
        self.connect(file)

    """ Creates Binance client """

    def connect(self, file):
        lines = [line.rstrip('\n') for line in open(file)]
        key = lines[0]
        secret = lines[1]
        self.client = Client(key, secret)

    """ Gets all account balances """

    def getBalances(self):
        prices = self.client.get_withdraw_history()
        return prices


filename = '../bots/config.py'
trader = Trader(filename)
TICKERS = '../bots/BVT/tickers_all.txt'


def get_symbols():
    response = requests.get('https://api.binance.com/api/v3/ticker/price')
    PAIRS_WITH = 'USDT'
    ignore = ['UP', 'DOWN', 'AUD', 'BRL', 'BVND', 'BUSD', 'BCC', 'BCHABC', 'BCHSV', 'BEAR', 'BNBBEAR', 'BNBBULL',
              'BULL',
              'BKRW', 'DAI', 'ERD', 'EUR', 'USDS', 'HC', 'LEND', 'MCO', 'GBP', 'RUB', 'TRY', 'NPXS', 'PAX', 'STORM',
              'VEN', 'UAH', 'USDC', 'NGN', 'VAI', 'STRAT', 'SUSD', 'XZC', 'RAD']
    symbols = []

    for symbol in response.json():
        if PAIRS_WITH in symbol['symbol'] and all(item not in symbol['symbol'] for item in ignore):
            if symbol['symbol'][-len(PAIRS_WITH):] == PAIRS_WITH:
                symbols.append(symbol['symbol'])
            symbols.sort()
    return symbols


with open(TICKERS) as f:
    trading_pairs = f.read().splitlines()
# trading_pairs = get_symbols()

filtered_pairs1 = []
filtered_pairs2 = []
filtered_pairs3 = []
selected_pair = []
selected_pairCMO = []


def filter1(pair):
    interval = '1h'
    symbol = pair
    klines = trader.client.get_klines(symbol=symbol, interval=interval)
    open_time = [int(entry[0]) for entry in klines]
    close = [float(entry[4]) for entry in klines]
    close_array = np.asarray(close)
    close_series = pd.Series(close)

    print("on 1h timeframe " + symbol)

    x = close
    y = range(len(x))
    real = pta.cmo(close_series, talib=False)
    print(real.iat[-1])

    best_fit_line1 = np.poly1d(np.polyfit(y, x, 1))(y)
    best_fit_line2 = (np.poly1d(np.polyfit(y, x, 1))(y)) * 1.01
    best_fit_line3 = (np.poly1d(np.polyfit(y, x, 1))(y)) * 0.99

    if real.iat[-1] < -60 and x[-1] < best_fit_line3[-1] and best_fit_line1[0] <= best_fit_line1[-1]:
        filtered_pairs1.append(symbol)
        print('found')

        plt.figure(figsize=(8, 6))
        plt.grid(True)
        plt.plot(x)
        plt.title(label=f'{symbol}', color="green")
        plt.plot(best_fit_line1, '--', color='r')
        plt.plot(best_fit_line2, '--', color='r')
        plt.plot(best_fit_line3, '--', color='green')
        plt.show(block=False)
        plt.pause(6)
        plt.close()

    elif real.iat[-1] < -60 and x[-1] < best_fit_line3[-1] and best_fit_line1[0] >= best_fit_line1[-1]:
        filtered_pairs1.append(symbol)
        print('found')

        plt.figure(figsize=(8, 6))
        plt.grid(True)
        plt.plot(x)
        plt.title(label=f'{symbol}', color="green")
        plt.plot(best_fit_line1, '--', color='r')
        plt.plot(best_fit_line2, '--', color='r')
        plt.plot(best_fit_line3, '--', color='green')
        plt.show(block=False)
        plt.pause(6)
        plt.close()

    else:
        print('searching')


def filter2(filtered_pairs1):
    interval = '15m'
    symbol = filtered_pairs1
    klines = trader.client.get_klines(symbol=symbol, interval=interval)
    open_time = [int(entry[0]) for entry in klines]
    close = [float(entry[4]) for entry in klines]
    close_array = np.asarray(close)

    print("on 15min timeframe " + symbol)

    x = close
    y = range(len(x))

    best_fit_line1 = np.poly1d(np.polyfit(y, x, 1))(y)
    best_fit_line2 = (np.poly1d(np.polyfit(y, x, 1))(y)) * 1.01
    best_fit_line3 = (np.poly1d(np.polyfit(y, x, 1))(y)) * 0.99

    if x[-1] < best_fit_line3[-1] and best_fit_line1[0] < best_fit_line1[-1]:
        filtered_pairs2.append(symbol)
        print('found')

        # plt.figure(figsize=(8, 6))
        # plt.grid(True)
        # plt.plot(x)
        # plt.title(label=f'{symbol}', color="green")
        # plt.plot(best_fit_line1, '--', color='r')
        # plt.plot(best_fit_line2, '--', color='r')
        # plt.plot(best_fit_line3, '--', color='r')
        # plt.show(block=False)
        # plt.pause(6)
        # plt.close()

    if x[-1] < best_fit_line3[-1] and best_fit_line1[0] >= best_fit_line1[-1]:
        filtered_pairs2.append(symbol)
        print('found')

        # plt.figure(figsize=(8, 6))
        # plt.grid(True)
        # plt.plot(x)
        # plt.title(label=f'{symbol}', color="green")
        # plt.plot(best_fit_line1, '--', color='r')
        # plt.plot(best_fit_line2, '--', color='r')
        # plt.plot(best_fit_line3, '--', color='r')
        # plt.show(block=False)
        # plt.pause(6)
        # plt.close()


def filter3(filtered_pairs2):
    interval = '5m'
    symbol = filtered_pairs2
    klines = trader.client.get_klines(symbol=symbol, interval=interval)
    open_time = [int(entry[0]) for entry in klines]
    close = [float(entry[4]) for entry in klines]
    close_array = np.asarray(close)
    close_series = pd.Series(close)

    print("on 5m timeframe " + symbol)

    # min = ta.MIN(close_array, timeperiod=30)
    max = close_series.rolling(30).max()
    min = close_series.rolling(30).min()
    # max = ta.MAX(close_array, timeperiod=30)

    # real = ta.HT_TRENDLINE(close_array)
    # wcl = ta.WCLPRICE(max, min, close_array)

    print(close[-1])
    print()
    print(min.iat[-1])
    print(max.iat[-1])
    # print(real[-1])

    x = close
    y = range(len(x))

    best_fit_line1 = np.poly1d(np.polyfit(y, x, 1))(y)
    best_fit_line2 = (np.poly1d(np.polyfit(y, x, 1))(y)) * 1.01
    best_fit_line3 = (np.poly1d(np.polyfit(y, x, 1))(y)) * 0.99

    if x[-1] < best_fit_line3[-1]:
        filtered_pairs3.append(symbol)
        print('found')

        plt.figure(figsize=(8, 6))
        plt.title(symbol)
        plt.grid(True)
        plt.plot(close)
        plt.title(label=f'{symbol}', color="green")
        plt.plot(best_fit_line1, '--', color='r')
        plt.plot(best_fit_line2, '--', color='r')
        plt.plot(best_fit_line3, '--', color='r')
        plt.plot(close)
        plt.plot(min)
        plt.plot(max)
        # plt.plot(real)
        plt.show(block=False)
        plt.pause(10)
        plt.close()

    else:
        print('searching')


def momentum(filtered_pairs3):
    interval = '1m'
    symbol = filtered_pairs3
    # klines = client.get_klines(symbol=symbol, interval=interval)
    # open_time = [int(entry[0]) for entry in klines]
    # close = [float(entry[4]) for entry in klines]
    # close_array = pd.Series(close)
    # real = pta.cmo(close_array, talib=False)

    start_str = '12 hours ago UTC'
    end_str = f'{datetime.now()}'
    # print(f"Fetching new bars for {datetime.now().isoformat()}")
    df = pd.DataFrame(client.get_historical_klines(symbol, interval, start_str, end_str)[:-1]).astype(float)
    df = df.iloc[:, :6]
    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    df = df.set_index('timestamp')
    df.index = pd.to_datetime(df.index, unit='ms')
    # CMO
    real = pta.cmo(df.close, talib=False)
    # WaveTrend
    n1 = 10
    n2 = 21
    ap = pta.hlc3(df.high, df.low, df.close)
    esa = pta.ema(ap, n1)
    d = pta.ema(abs(ap - esa), n1)
    ci = (ap - esa) / (0.015 * d)
    wt1 = pta.ema(ci, n2)
    #
    print("on 1m timeframe " + symbol)
    print(f'cmo: {real.iat[-1]}')
    print(f'wt1: {wt1.iat[-1]}')

    if real.iat[-1] < -50 and wt1.iat[-1] < -60:
        print('oversold dip found')
        selected_pair.append(symbol)
        selected_pairCMO.append(real.iat[-1])

    return selected_pair


for i in trading_pairs:
    output = filter1(i)
    print(filtered_pairs1)

for i in filtered_pairs1:
    output = filter2(i)
    print(filtered_pairs2)

for i in filtered_pairs2:
    output = filter3(i)
    print(filtered_pairs3)

for i in filtered_pairs3:
    output = momentum(i)
    print(selected_pair)

if len(selected_pair) > 1:
    print('dips are more then 1 oversold')
    print(selected_pair)
    print(selected_pairCMO)

    if min(selected_pairCMO) in selected_pairCMO:
        print(selected_pairCMO.index(min(selected_pairCMO)))
        position = selected_pairCMO.index(min(selected_pairCMO))

    for id, value in enumerate(selected_pair):
        if id == position:
            print(selected_pair[id])
    sys.exit()

elif len(selected_pair) == 1:
    print('1 dip found')
    print(selected_pair)
    print(selected_pairCMO)
    sys.exit()

else:
    print('no oversold dips for the moment, restart script...')
    print(selected_pair)
    print(selected_pairCMO)
    time.sleep(60)
    os.execl(sys.executable, sys.executable, *sys.argv)

# sys.exit(0)
sys.exit() if KeyboardInterrupt else exit()
# exit()
