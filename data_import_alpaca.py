# %%
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import Adjustment

from datetime import datetime


with open("alpaca_secret.txt") as f:
    PUBLIC_KEY = next(f).strip()
    PRIVATE_KEY = next(f).strip()

stock_client = StockHistoricalDataClient(PUBLIC_KEY, PRIVATE_KEY)

stock_request = StockBarsRequest(
    symbol_or_symbols=["AREX", "WLL"],
    start=datetime(2017, 1, 1),
    end=datetime(2017, 12, 31),
    timeframe=TimeFrame(5, TimeFrameUnit.Minute),
    adjustment=Adjustment.ALL,
)
bars = stock_client.get_stock_bars(stock_request).df

# %%

arex_stock = bars.loc["AREX"][["open", "high", "low", "close", "volume"]]
arex_stock.index.names = ["datetime"]
arex_stock.set_index(arex_stock.index.tz_convert("US/Eastern"), inplace=True)
arex_stock = arex_stock.between_time(
    "9:30", "16:00"
)  # For simplicity: in reality market is not always open between 9:30 and 16:00 ET...
arex_stock.set_index(arex_stock.index.tz_convert("UTC"), inplace=True)
arex_stock["adj_close"] = arex_stock["close"]
arex_stock = arex_stock[["open", "high", "low", "close", "adj_close", "volume"]]
arex_stock.to_csv("../data/yahoo/AREX.csv")

wll_stock = bars.loc["WLL"][["open", "high", "low", "close", "volume"]]
wll_stock.index.names = ["datetime"]
wll_stock.set_index(wll_stock.index.tz_convert("US/Eastern"), inplace=True)
wll_stock = wll_stock.between_time("9:30", "16:00")
wll_stock.set_index(wll_stock.index.tz_convert("UTC"), inplace=True)
wll_stock["adj_close"] = wll_stock["close"]
wll_stock = wll_stock[["open", "high", "low", "close", "adj_close", "volume"]]
wll_stock.to_csv("../data/yahoo/WLL.csv")


# %%
