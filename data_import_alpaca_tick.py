"""
Goal: acquire SPY tick data and convert them to 1-minute OHLC quote bars with
(time, open, high, low, close, close_bid, close_ask, volume)
"""
# %%
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockQuotesRequest
from datetime import datetime
from pytz import timezone

# %% DOWNLOAD TICK DATA & SAVE TO CSV

with open("alpaca_secret.txt") as f:
    PUBLIC_KEY = next(f).strip()
    PRIVATE_KEY = next(f).strip()

start_date_naive = datetime(2023, 7, 21, 9, 30)  # in ET
start_date_aware = timezone("US/Eastern").localize(start_date_naive)

end_date_naive = datetime(2023, 7, 21, 10, 30)  # in ET
end_date_aware = timezone("US/Eastern").localize(end_date_naive)

stock_client = StockHistoricalDataClient(PUBLIC_KEY, PRIVATE_KEY)

stock_request = StockQuotesRequest(
    symbol_or_symbols=["SPY"], start=start_date_aware, end=end_date_aware
)
ticks = stock_client.get_stock_quotes(stock_request)
ticks.df.to_csv("ticks.csv")

# %% ANALYZE TICK DATA


# %% CONVERT TO QUOTE BARS & SAVE TO CSV
