from tracemalloc import start
import alpaca_trade_api as tradeapi
import pandas_ta as ta
import math
import operator
import pandas as pd

APCA_API_KEY_ID = "ENTER YOUR API KEY HERE"
APCA_API_SECRET_KEY = "ENTER YOUR SECRET KEY HERE"
APCA_API_BASE_URL = "https://paper-api.alpaca.markets"

api = tradeapi.REST(key_id=APCA_API_KEY_ID, secret_key=APCA_API_SECRET_KEY, base_url=APCA_API_BASE_URL)

# Back Test Parameters:
# sym - ticker
# buy - needs to be a function of metric a, b, and operator [sma, lt, cur_price] *using operator module for gt, lt operators etc.
# sell - needs to be function of metric a, b, and operator [sma, gt, cur_price] *using operator module for gt, lt operators etc.
# start date - start date in "YYYY-MM-DD" format
# end date - endate in "YYYY-MM-DD" format
# starting_balance - starting capital

# supported metrics in strategy
# SMA 10,50, BBANDS, RSI, MACD (12,26)

CustomStrategy = ta.Strategy(
    name="TA Metrics",
    description="SMA 10,50 BBANDS, RSI, and MACD",
    ta=[
        {"kind": "sma", "length": 10},
        {"kind": "sma", "length": 50},
        {"kind": "bbands", "length": 20},
        {"kind": "rsi"},
        {"kind": "macd", "fast": 12, "slow": 26},
    ]
)

# can use "col_names": in TA objects to set a custom name for columns
# i.e. {"kind": "macd", "fast": 12, "slow": 26, "col_names": ("MACD", "MACD_H", "MACD_S")}

def backtest(sym, date_start, date_end, starting_balance=0, buy=[], sell=[]):
    # currently defaulted to a day time frame, but this can be changed to hour, minute, etc depending on what you wish to backtest
    df = api.get_bars(sym, tradeapi.rest.TimeFrame.Day, date_start, date_end, adjustment='raw').df
    df.reset_index(inplace=True)
    df.ta.strategy(CustomStrategy)

    running_balance = starting_balance
    open_position = False
    open_quantity = 0

    for i in range(0, df.shape[0]):

        if (pd.isnull(df.iloc[i][buy[0]]) or pd.isnull(df.iloc[i][buy[2]])):
            pass

        else:
            if buy[1](df.iloc[i][buy[0]], df.iloc[i][buy[2]]) and open_position == False:
                price = df.iloc[i]['close']
                open_quantity = math.floor((running_balance-1000)/price)
                cost =  price * open_quantity
                running_balance -= cost
                open_position = True
                print(f'Bought {open_quantity} {sym} @ ${price}')
                print(f'New Balance: ${running_balance}')

            elif sell[1](df.iloc[i][sell[0]], df.iloc[i][sell[2]]) and open_position == True:
                price = df.iloc[i]['close']
                proceeds = price * open_quantity
                running_balance += proceeds
                open_position = False
                print(f'Sold {open_quantity} {sym} @ ${price}')
                open_quantity = 0
                print(f'New Balance: ${running_balance}')

    print(f'Starting Balance: {starting_balance}')
    print(f'Ending Balance: {running_balance}')

    equity_value = open_quantity * df.iloc[df.shape[0]-1]['close']
    if equity_value == 0:
        total_return = (running_balance - starting_balance) / starting_balance *100
    else:
        total_return = (equity_value + running_balance - starting_balance) / starting_balance *100
    print(f'Total Returns: {equity_value + running_balance - starting_balance} or {total_return}%')


# this is required for multiprocessing on windows
if __name__ == '__main__':
    backtest("AAPL", "2021-01-08", "2022-01-08",  50000, ["MACD_12_26_9", operator.gt, "MACDs_12_26_9"], ["MACD_12_26_9", operator.lt, "MACDs_12_26_9"])
    
