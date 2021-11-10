import pandas as pd
from tqdm import tqdm
from binance.client import Client

client = Client()

info = client.get_exchange_info()
symbols = [x['symbol'] for x in info['symbols']]
exclude = ['UP', 'DOWN', 'BEAR', 'BULL']
non_lev = [symbol for symbol in symbols if all(ex not in symbol for ex in exclude)]
relevant = [symbol for symbol in non_lev if symbol.endswith('USDT')]
klines = {}
for symbol in tqdm(relevant):
    klines[symbol] = client.get_historical_klines(symbol, '1h', '24 hours ago UTC')

returns, symbols = [], []

for symbol in relevant:
    if len(klines[symbol]) > 0:
        cumret = (pd.DataFrame(klines[symbol])[4].astype(float).pct_change() + 1).prod() - 1
        returns.append(cumret * 100)
        symbols.append(symbol)

retdf = pd.DataFrame(returns, index=symbols, columns=['ret'])
top = retdf.ret.nlargest(10)
print(top)
