import pandas as pd

data = pd.read_csv('banknifty.csv')
data.head(20)
close = data['close']
entry = close[0]
initalSL = entry + 60
trail = 10
forwardMove = 20
SL = initalSL
print('Entry: ', entry, 'SL : ', initalSL)

for i in range(0, len(close) - 1):

    diff = round((entry - close[i]), 2)
    point = int(diff / forwardMove) if diff > 0 else 0
    SLmove = point * trail

    if initalSL - SL < SLmove:
        SL = initalSL - SLmove  # SL ORDER UPDATE HERE
        print(f'{i} {data.loc[i]["datetime"]} close {close[i]} New SL  {SL}  diff {diff} ')  # {point}  {SLmove}')
    elif SL <= close[i]:
        print('SL hit : ', data.loc[i]["datetime"], close[i], ' ', SL)
        break
    else:
        print(f'{i} {data.loc[i]["datetime"]} close {close[i]} SL  {SL} diff {diff} ')

data = data[7:].reset_index()
close = data['close']
entry = close[0]
initalSL = entry - 60
trail = 20
forwardMove = 20
print(f'{initalSL} {entry}')
SL = initalSL
for i in range(0, len(close) - 1):

    diff = round((close[i] - entry), 2)
    point = int(diff / forwardMove) if diff > 0 else 0
    SLmove = point * trail
    if SL >= close[i]:
        print('SL hit : ', data.loc[i]["datetime"], close[i], ' ', SL)
        break
    elif SL - initalSL < SLmove:
        SL = initalSL + SLmove  # ORDER UPDATE HERE
        print(f'{i} {data.loc[i]["datetime"]} New SL {SL} {point}  {SLmove}')
    else:
        print(f'{i} {data.loc[i]["datetime"]} close {close[i]} SL  {SL} diff {diff} ')
