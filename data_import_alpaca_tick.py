"""
Gets tick data and converts them to 1-minute OHLC quote (bid/ask) bars.
"""
# %%
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockQuotesRequest
from datetime import datetime
from pytz import timezone

# %% 1. DOWNLOAD TICK DATA & SAVE TO CSV
STOCK = "O"
START_DATE = datetime(2023, 1, 25, 4)  # in ET
END_DATE = datetime(2023, 2, 5, 22)  # in ET


with open("alpaca_secret.txt") as f:
    PUBLIC_KEY = next(f).strip()
    PRIVATE_KEY = next(f).strip()

start_date_naive = START_DATE
start_date_aware = timezone("US/Eastern").localize(start_date_naive)

end_date_naive = END_DATE
end_date_aware = timezone("US/Eastern").localize(end_date_naive)

stock_client = StockHistoricalDataClient(PUBLIC_KEY, PRIVATE_KEY)

stock_request = StockQuotesRequest(
    symbol_or_symbols=STOCK, start=start_date_aware, end=end_date_aware
)
ticks = stock_client.get_stock_quotes(stock_request)
ticks.df.to_csv(f"../data/alpaca/raw/tick/{STOCK}.csv")

# %% ANALYZE TICK DATA


# %% CONVERT TO QUOTE BARS & SAVE TO CSV
