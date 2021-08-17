import websocket
import json
import time
import ccxt
import pandas_ta as ta
import pandas as pd
import config
import logging
import telebot
import warnings
from binance.client import Client
from datetime import datetime

exchange = ccxt.binance({
    "apiKey": config.BINANCE_API_KEY2,
    "secret": config.BINANCE_SECRET_KEY2,
    "timeout": 50000,
    "enableRateLimit": True
})

pd.set_option('display.max_columns', 30)
warnings.filterwarnings('ignore')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
CHAT_ID = config.CHAT_ID
bot = telebot.TeleBot(config.TELEGRAM_TOKEN)

symbol = 'BNBUSDT'
symbol1 = 'BNB/USDT'
amount = 0.20
TRADE_QUANTITY = 1
multiplier = 2.0
length = 3
interval = '30m'
in_position = True
SOCKET = f"wss://stream.binance.com:9443/ws/bnbusdt@kline_{interval}"

client = Client(config.BINANCE_API_KEY, config.BINANCE_SECRET_KEY)

print(f"Fetching new bars for {datetime.now().isoformat()}")
data = client.get_historical_klines(symbol, interval, '10 day ago UTC')
df = pd.DataFrame(data).astype(float)
df_edited = df.drop([0, 5, 6, 7, 8, 9, 10, 11], axis=1)
df_final = df_edited.drop(df_edited.tail(1).index)
df_final.columns = ['o', 'h', 'l', 'c']


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


# TELEBOT functions
def telebot_sell_data(order):
    json_d = json.dumps(order)
    json_ = json.loads(json_d)
    typeorder = json_['info']['type']
    price_sell = json_['price']
    qty = json_['amount']
    cost = json_['cost']
    fee = json_['fee']['cost']
    bot.send_message(CHAT_ID, f'\u274C {symbol} supertrend down - SELL \ntype: {typeorder}\nprice: {price_sell}\n'
                              f'amount: {qty}\ncost: {cost} USDT\nfee: {fee} BNB')


def telebot_buy_data(order_buy):
    json_d = json.dumps(order_buy)
    json_ = json.loads(json_d)
    typeorder = json_['info']['type']
    price_buy = json_['price']
    qty = json_['amount']
    cost = json_['cost']
    fee = json_['fee']['cost']
    bot.send_message(CHAT_ID, f'\u274E {symbol} supertrend up - BUY \ntype: {typeorder}\nprice: {price_buy}\n'
                              f'amount: {qty}\ncost: {cost} USDT\nfee: {fee} BNB')


def telebot_sl_data(sl):
    json_d = json.dumps(sl)
    json_ = json.loads(json_d)
    typeorder = json_['info']['type']
    stop_price = json_['info']['stopPrice']
    pricesl = json_['info']['price']
    qty = json_['amount']
    bot.send_message(CHAT_ID, f'\u26D4 {symbol}\ntype: {typeorder}\nstop price: {float(stop_price)}\n'
                              f'price: {float(pricesl)}\n'
                              f'amount: {qty}\n')


@bot.message_handler(commands=['bnb'])
def bnb_balance(message):
    CHAT_ID = message.chat.id
    balance = exchange.fetch_balance()
    bnbbalance = balance['free']['BNB']
    bot.send_message(CHAT_ID, bnbbalance)


@bot.message_handler(commands=['usdt'])
def usdt_balance(message):
    CHAT_ID = message.chat.id
    balance = exchange.fetch_balance()
    usdtbalance = balance['free']['USDT']
    bot.send_message(CHAT_ID, usdtbalance)


def on_open(ws):
    print('Receiving data...')


def on_close(ws):
    print('closed connection')


def on_error(ws, err):
    print("Got a an error: ", err)


def on_message(ws, message):
    global df_final
    global in_position

    json_message = json.loads(message)
    candle = json_message['k']
    candle_closed = candle['x']
    open_data = candle['o']
    high_data = candle['h']
    low_data = candle['l']
    close_data = candle['c']
    # print(candle)

    if candle_closed:
        df_final = df_final.append(candle, ignore_index=True)
        df_final = df_final.drop(['i', 'n', 'x', 's', 'q', 't', 'v', 'B', 'L', 'Q', 'T', 'V', 'f'], axis=1)
        df_final.o = df_final.o.astype(float)
        df_final.h = df_final.h.astype(float)
        df_final.l = df_final.l.astype(float)
        df_final.c = df_final.c.astype(float)
        # HEIKIN ASHI
        df_final_ha = ta.ha(df_final['o'], df_final['h'], df_final['l'], df_final['c'])

        df_final_ha = df_final_ha.set_axis(['o', 'h', 'l', 'c'], axis=1)  # change column name
        # df_final = round(df_final, 4)
        df_final_ha['sup'] = \
            ta.supertrend(high=df_final_ha['h'], low=df_final_ha['l'], close=df_final_ha['c'], length=length,
                          multiplier=multiplier)[f'SUPERT_{length}_{multiplier}']
        # Supertrend signals
        df_final_ha['Buy_Signal'] = 0
        df_final_ha['Sell_Signal'] = 0
        n = (length - 1)
        for i in range(n, len(df_final_ha)):
            if df_final_ha['c'][i - 1] <= df_final_ha['sup'][i - 1] and df_final_ha['c'][i] > df_final_ha['sup'][i]:
                df_final_ha['Buy_Signal'][i] = 1
            if df_final_ha['c'][i - 1] >= df_final_ha['sup'][i - 1] and df_final_ha['c'][i] < df_final_ha['sup'][i]:
                df_final_ha['Sell_Signal'][i] = 1
        # print(df_final_ha.tail(4))

        last_open = round(df_final_ha['o'].tail(1), 4)
        last_high = df_final_ha['h'].tail(1)
        last_low = df_final_ha['l'].tail(1)
        last_close = df_final_ha['c'].tail(1)
        last_sup = round(df_final_ha['sup'].tail(1), 2)
        last_buy = df_final_ha['Buy_Signal'].tail(1)
        last_sell = df_final_ha['Sell_Signal'].tail(1)

        print(
            f"Open: {float(last_open)} | High: {float(last_high)} | Low: {float(last_low)} | Close: {float(last_close)}")
        print(f'SUPERTREND: {float(last_sup)}')

        bot.send_message(CHAT_ID,
                         f"{symbol1}\nOpen: {float(last_open)} | High: {float(last_high)} | Low: {float(last_low)} | "
                         f"Close: {float(last_close)}\n"
                         f"SUPERTREND_{length}_{multiplier}: {float(last_sup)}\n"
                         f"Buy Signal = {int(last_buy)}\n"
                         f"Sell Signal = {int(last_sell)}")

        # trading strategy
        # price = df_final['c'].tail(1)
        # price_sl = price - (price * 0.036)  # -3,6%
        # stopPrice = price - (price * 0.035)
        if int(last_buy) > 0:
            print(f"changed to uptrend, BUY {symbol}")
            if not in_position:
                # order = exchange.create_limit_buy_order(symbol1, amount, df['close'][last_row_index])
                order_buy = exchange.create_market_buy_order(symbol=symbol1, amount=amount)
                print(order_buy)
                telebot_buy_data(order_buy)
                json_d = json.dumps(order_buy)
                json_ = json.loads(json_d)
                price = float(json_['price'])
                price_sl = price - (price * 0.036)  # -3,6%
                stopPrice = price - (price * 0.035)
                time.sleep(2)
                sl = exchange.create_order(symbol=symbol1, type='stop_loss_limit',
                                           side='sell', amount=amount, price=price_sl,
                                           params={'stopPrice': stopPrice})
                print(sl)
                telebot_sl_data(sl)
                in_position = True
            else:
                print("already in position, nothing to do")
                bot.send_message(CHAT_ID, f'\u274E {symbol} supertrend up but already in position')

        if int(last_sell) > 0:
            if in_position and get_open_orders():
                print(f"SUPERTREND changed to downtrend, SELL {symbol1}")
                cancel_all_orders()
                order = exchange.create_market_sell_order(symbol1, amount)
                print(order)
                # bot.send_message(CHAT_ID, f'\u274C {symbol} supertrend down - SELL \n{order}')
                telebot_sell_data(order)
                in_position = False
            elif in_position and not get_open_orders():
                print("SUPERTREND changed to downtrend but already not in position")
                bot.send_message(CHAT_ID, f'\u274C {symbol} supertrend down but already not in position')
                in_position = False
            else:
                print("You aren't in position, nothing to sell")
                bot.send_message(CHAT_ID, f'\u274C {symbol} supertrend down but already not in position')


websocket.setdefaulttimeout(60)
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message, on_error=on_error)

while True:
    try:
        ws.run_forever()
        # bot.polling(none_stop=True)
        time.sleep(5)
    except Exception:
        print("==> ConnectionResetByPeerError")
    pass
