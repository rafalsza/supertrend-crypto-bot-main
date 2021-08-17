import pandas_ta as ta
import math
import xlwt
from termcolor import colored as cl
import pandas as pd
import numpy as np
import warnings
from datetime import datetime
from binance import Client
from xlrd import open_workbook
from xlutils.copy import copy
import ccxt

exchange = ccxt.gateio({
    "apiKey": '',
    "secret": '',
    "timeout": 50000,
    "enableRateLimit": True
})

warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', 30)

client = Client("", "")
coin = 'LTC'
symbol = coin + 'USDT'
raw = 74  # index of raw xls
sheet_number = 0  # index of sheet xls
multiplier = 5.3
length = 3
interval = '1h'
# start_str = '30 days ago UTC'
start_str = '6 months ago UTC'
end_str = f'{datetime.now()}'


# end_str = '05-07-2021'

# f'{datetime.now()}'


def backtest():
    print(f"Fetching new bars for {datetime.now().isoformat()}")
    candlesticks = client.get_historical_klines(symbol, interval, start_str, end_str)
    # trim each candle
    for candle in candlesticks:
        del candle[-6:]  # only need the first few columns
    df = pd.DataFrame(candlesticks[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']).astype(float)
    # bars = exchange.fetch_ohlcv(symbol1, interval, limit=200)
    # df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index(pd.DatetimeIndex(df['timestamp'].values))
    normal_candle = df['close']
    # HEIKIN_ASHI
    df = ta.ha(df['open'], df['high'], df['low'], df['close'])
    df = pd.concat([df, normal_candle], axis=1)
    # SUPERTREND
    df['sup'] = \
        ta.supertrend(high=df['HA_high'], low=df['HA_low'], close=df['HA_close'], length=length, multiplier=multiplier)[
            f'SUPERT_{length}_{multiplier}']
    # df = round(df, 6)

    df['Buy_Signal'] = 0
    df['Sell_Signal'] = 0
    n = (length - 1)
    for i in range(n, len(df)):
        if df['HA_close'][i - 1] <= df['sup'][i - 1] and df['HA_close'][i] > df['sup'][i]:
            df['Buy_Signal'][i] = 1
        if df['HA_close'][i - 1] >= df['sup'][i - 1] and df['HA_close'][i] < df['sup'][i]:
            df['Sell_Signal'][i] = 1
    df_final = df[(df['Buy_Signal'] > 0) | (df['Sell_Signal'] > 0)]
    # df = df.drop(index=df.index[[0, 1, 2, 3, 4, 5, 6, 7]])

    # balance = exchange.fetch_balance()
    # print('---BNB------')
    # print(balance['free']['BNB'])
    # print('----USDT----')
    # print(balance['free']['USDT'])
    # Calculate Returns and append to the df DataFrame

    # df['percent'] = ta.percent_return(df['HA_close'], cumulative=True, append=True)

    # BACKTESTING
    strategy = df_final
    investment_value = 1000
    if (strategy.at[strategy.index[0], 'Sell_Signal']) == 1:
        strategy = strategy.iloc[1:]
    amount = round(investment_value / (strategy.at[strategy.index[0], 'close']), 6)  # Stocks
    strategy['profit_amount'] = round((strategy.loc[strategy.index[1:], 'close'] * amount), 4)
    strategy.loc[strategy.index[0], 'profit_amount'] = round((strategy.loc[strategy.index[0], 'close'] * amount), 4)
    # strategy['profit_amount'] = round((strategy['close'] * amount), 4)
    strategy['total_profit_amount'] = round((strategy.shift(-1).profit_amount - strategy.profit_amount), 4)
    strategy['total_profit'] = round((strategy.shift(-1).close - strategy.close), 6)
    strategy['total_percent'] = round(((strategy.shift(-1).close - strategy.close) / strategy.close) * 100, 2)

    # else:
    #     strategy = strategy[::2]
    orders_number = strategy['total_percent'].count()
    strategy = strategy[::2]
    strategy = strategy.dropna()
    total_investment_ret = round(sum(strategy['total_profit_amount']), 2)
    profit_percentage = round(sum(strategy['total_percent']), 2)
    strategy.to_excel("output.xlsx")

    print(f'SUPERT_{length}_{multiplier}')
    print(f"Profit percentage of the ST strategy for {coin} : {profit_percentage} % | backtest time: {start_str} | "
          f"interval:{interval}")
    print("Positive:",
          strategy[strategy['total_percent'] > 0]['total_percent'].count(),
          "Negative:", strategy[strategy['total_percent'] < 0]['total_percent'].count())

    strategy.loc[strategy['total_percent'] < -5, 'total_percent'] = -5

    profit_percentage_sl = round(sum(strategy['total_percent']), 2)

    print(f"Profit percentage of the ST strategy with SL 5% for {coin} : {profit_percentage_sl} %")
    print(f'Total profit (invested 1000$):{total_investment_ret}')

    # Workbook is created
    ratio = round((strategy[strategy['total_percent'] > 0]['total_percent'].count()) /
                  (strategy[strategy['total_percent'] < 0]['total_percent'].count()), 2)

    rb = open_workbook("backtest.xls", formatting_info=True)
    wb = copy(rb)
    # wb = Workbook()
    style_value = xlwt.easyxf('font: bold 1')
    sheet1 = wb.get_sheet(sheet_number)

    # add_sheet is used to create sheet.
    sheet1.write(0, 0, 'Time', style_value)
    sheet1.write(0, 1, 'SUPERT', style_value)
    sheet1.write(0, 2, 'COIN', style_value)
    sheet1.write(0, 3, 'Profit %', style_value)
    sheet1.write(0, 4, 'Profit SL 5%', style_value)
    sheet1.write(0, 5, 'Interval', style_value)
    sheet1.write(0, 6, 'Orders number', style_value)
    sheet1.write(0, 7, 'Win/Loss Ratio', style_value)
    sheet1.write(0, 10, 'Profit $', style_value)

    sheet1.write(raw, 0, start_str)
    sheet1.write(raw, 1, f'SUPERT_{length}_{multiplier}')
    sheet1.write(raw, 2, coin)
    sheet1.write(raw, 3, profit_percentage)
    sheet1.write(raw, 4, profit_percentage_sl)
    sheet1.write(raw, 5, interval)
    sheet1.write(raw, 6, int(orders_number))
    sheet1.write(raw, 7, ratio)
    sheet1.write(raw, 10, total_investment_ret)

    # SPY ETF COMPARISON
    def get_benchmark(investment_value_rtf):
        close_etf = df['close']
        benchmark = pd.DataFrame(np.diff(close_etf)).rename(columns={0: 'benchmark_returns'})

        investment_value_etf = investment_value_rtf
        number_of_stocks_etf = math.floor(investment_value_etf / close_etf[-1])
        benchmark_investment_ret = []

        for i in range(len(benchmark['benchmark_returns'])):
            returns_etf = number_of_stocks_etf * benchmark['benchmark_returns'][i]
            benchmark_investment_ret.append(returns_etf)

        benchmark_investment_ret_df = pd.DataFrame(benchmark_investment_ret).rename(columns={0: 'investment_returns'})
        return benchmark_investment_ret_df

    benchmark = get_benchmark(10000)
    investment_value_etf = 10000
    total_benchmark_investment_ret = round(sum(benchmark['investment_returns']), 2)
    df['percent'] = (ta.percent_return(df['close'], cumulative=True, append=True)) * 100
    df['percent'] = round(df['percent'], 2)
    benchmark_profit_percentage = df['percent'].iloc[-1]
    # benchmark_profit_percentage = math.floor((total_benchmark_investment_ret / investment_value_etf) * 100)
    print(cl('Benchmark profit by investing $1000 : {}'.format(total_benchmark_investment_ret), attrs=['bold']))
    print(cl('Benchmark Profit percentage : {}%'.format(benchmark_profit_percentage), attrs=['bold']))
    print(cl('ST Strategy profit is {}% higher than the Benchmark Profit'.format(
        round(profit_percentage - benchmark_profit_percentage), 2), attrs=['bold']))

    sheet1.write(0, 8, 'Benchmark %', style_value)
    sheet1.write(0, 9, 'Actual date', style_value)
    sheet1.write(raw, 8, benchmark_profit_percentage)
    sheet1.write(raw, 9, f'{datetime.now().date()}')

    wb.save('backtest.xls')


backtest()
