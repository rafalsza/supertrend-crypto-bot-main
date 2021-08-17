import ccxt
import time
import config
import pandas_ta as ta
import schedule
import pandas as pd
from binance import Client
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

exchange = ccxt.binance({
    "apiKey": config.BINANCE_API_KEY2,
    "secret": config.BINANCE_SECRET_KEY2,
    "timeout": 50000,
    "enableRateLimit": True
})

client = Client("", "")

# client = Client(api_key=config.BINANCE_API_KEY2, api_secret=config.BINANCE_SECRET_KEY2)
symbol = 'BNBUSDT'
symbol1 = 'BNB/USDT'
amount = 0.15
multiplier = 2.0
length = 3
interval = '30m'


def get_open_orders():
    orders = []
    try:
        orders = exchange.fetch_open_orders(symbol1)
    except ccxt.ExchangeError:
        print('Error. Could not fetch orders.')

    return orders


def cancel_all_orders():
    orders = get_open_orders()
    if orders:
        exchange.cancel_all_orders(symbol1)
        print('All orders canceled.')
    else:
        print('No open orders.')


in_position = False


def check_buy_sell_signals(df):
    global in_position

    print("checking for buy and sell signals")
    print(df.tail(6))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1
    price = df['close'][last_row_index]
    price_sl = price - (price * 0.036)   # -3,6%
    stopPrice = price - (price * 0.035)

    if df['Buy_Signal'][previous_row_index] == 0 and df['Buy_Signal'][last_row_index] == 1:
        print(f"changed to uptrend, BUY {symbol}")
        if not in_position:
            # order = exchange.create_limit_buy_order(symbol1, amount, df['close'][last_row_index])
            order = exchange.create_market_buy_order(symbol=symbol1, amount=amount)
            time.sleep(3)
            sl = exchange.create_order(symbol=symbol1, type='stop_loss_limit',
                                       side='sell', amount=amount, price=price_sl,
                                       params={'stopPrice': stopPrice})
            print(order)
            print(sl)
            in_position = True
        else:
            # if in_position and sl.get('status') == 'closed':
            #     in_position = False
            print("already in position, nothing to do")

    if df['Sell_Signal'][previous_row_index] == 0 and df['Sell_Signal'][last_row_index] == 1:
        # if in_position_without_sl:
        #     print("changed to downtrend, sell")
        #     order = exchange.create_market_sell_order(symbol1, 0.15)
        #     print(order)
        #     in_position = False
        if in_position and get_open_orders():
            print(f"SUPERTREND changed to downtrend, SELL {symbol1}")
            cancel_all_orders()
            order = exchange.create_market_sell_order(symbol1, amount)
            print(order)
            in_position = False
        elif in_position and not get_open_orders():
            print("SUPERTREND changed to downtrend but already not in position")
            in_position = False
        else:
            print("You aren't in position, nothing to sell")


def run_bot():
    print(f"Fetching new bars for {datetime.now().isoformat()}")
    candlesticks = client.get_historical_klines(symbol, interval, '10 day ago UTC')
    # trim each candle
    for candle in candlesticks:
        del candle[-6:]  # only need the first few columns
    df = pd.DataFrame(candlesticks[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']).astype(float)
    # bars = exchange.fetch_ohlcv(symbol1, timeframe='30m', limit=200)
    # df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index(pd.DatetimeIndex(df['timestamp'].values))
    # NORMAL CANDLE
    normal_candle = df['close']
    # HEIKIN ASHI
    df = ta.ha(df['open'], df['high'], df['low'], df['close'])
    # ADD NORMAL CANDLE to DATEFRAME
    df = pd.concat([df, normal_candle], axis=1)
    # SUPERTREND
    df['sup'] = ta.supertrend(high=df['HA_high'], low=df['HA_low'], close=df['HA_close'], length=length,
                              multiplier=multiplier)[
        f'SUPERT_{length}_{multiplier}']
    # ROUND to 4 DIGITS AFTER.
    df = round(df, 6)
    # BUY SIGNALS
    df['Buy_Signal'] = 0
    df['Sell_Signal'] = 0
    n = 2
    for i in range(n, len(df)):
        if df['HA_close'][i - 1] <= df['sup'][i - 1] and df['HA_close'][i] > df['sup'][i]:
            df['Buy_Signal'][i] = 1
        if df['HA_close'][i - 1] >= df['sup'][i - 1] and df['HA_close'][i] < df['sup'][i]:
            df['Sell_Signal'][i] = 1
    # df = df[(df['Buy_Signal'] > 0) | (df['Sell_Signal'] > 0)]

    check_buy_sell_signals(df)


schedule.every(30).seconds.do(run_bot)
while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except Exception:
        print("==> ConnectionResetByPeerError")
    pass
