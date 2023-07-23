"""
Gets 1 minute bars from Alpaca for a list of symbols, between market hours. 
Data is saved in ET and contains the rows ["open", "high", "low", "close", "volume", "tradeable"]
    tradable: False if no data available
    volume: 0 if no data available
    OHLC are adjusted for everything
"""
# %%
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import Adjustment

from datetime import datetime, time, timedelta
import pandas as pd
import numpy as np

# SETTINGS
SYMBOL_LIST = ["SPY", "TLT", "GLD", "SLV", "AAPL", "AMC", "GME", "WAL"]
START_DATE = datetime(2015, 12, 1)  # First date of available Alpaca data
END_DATE = datetime.utcnow() - timedelta(
    minutes=20
)  # We cannot query from past 15 minutes with a free subscription
TIMEFRAME = TimeFrame(1, TimeFrameUnit.Minute)
###
# %% 1. DOWNLOAD FROM ALPACA AND SAVE TO CSV
with open("alpaca_secret.txt") as f:
    PUBLIC_KEY = next(f).strip()
    PRIVATE_KEY = next(f).strip()

stock_client = StockHistoricalDataClient(PUBLIC_KEY, PRIVATE_KEY)

for stock in SYMBOL_LIST:
    stock_request = StockBarsRequest(
        symbol_or_symbols=stock,
        start=START_DATE,
        end=END_DATE,
        timeframe=TIMEFRAME,
        adjustment=Adjustment.ALL,
    )
    bars = stock_client.get_stock_bars(stock_request).df

    stock_df = bars.loc[stock][["open", "high", "low", "close", "volume"]]
    stock_df.index.names = ["datetime"]
    stock_df.to_csv(f"../data/alpaca/raw/m1/{stock}.csv")
    print(f"Downloaded {stock}")

# %% 2. LOAD FROM CSV AND PROCESS
MARKET_HOURS_ONLY = True
all_minutes = []
# Load raw data and process
for stock in SYMBOL_LIST:
    stock_df = pd.read_csv(
        f"../data/alpaca/raw/m1/{stock}.csv",
        index_col="datetime",
        parse_dates=True,
    )
    stock_df["tradeable"] = True

    # Convert from UTC to ET, remove timezone
    stock_df.set_index(stock_df.index.tz_convert("US/Eastern"), inplace=True)
    stock_df.set_index(stock_df.index.tz_localize(None), inplace=True)

    """
    US premarket is from 4:00 to 9:29
    US market hours are from 9:30 to 15:59
    US post market is from 16:00 to 19:59
    """
    # Problem: Some stocks do not have trades for all minutes the market is open. Especially since we source from IEX.
    # Solution: Get the market opening days from SPY. Then add all minutes to create a list of all timestamps the market is open. Then reindex using this list. Then fill missing values.
    if stock == "SPY" and len(all_minutes) == 0:
        dates = np.unique(pd.to_datetime(stock_df.index).date)
        amount_of_days = len(dates)
        for date in dates:
            for hour in range(4, 20):
                for minute in range(0, 60):
                    all_minutes.append(
                        datetime.combine(date, time(hour=hour, minute=minute))
                    )
        all_minutes = np.array(all_minutes)
        assert len(all_minutes) == amount_of_days * 16 * 60

    stock_df = stock_df.reindex(all_minutes)
    stock_df["tradeable"].fillna(False, inplace=True)
    stock_df["volume"].fillna(0, inplace=True)
    stock_df[["open", "high", "low", "close"]] = stock_df[
        ["open", "high", "low", "close"]
    ].fillna(method="ffill")

    # stock_df.dropna(inplace=True)
    # Only affects the very start. Else backfill shouldn't be used because of look-ahead bias.
    stock_df[["open", "high", "low", "close"]] = stock_df[
        ["open", "high", "low", "close"]
    ].fillna(method="bfill")

    if MARKET_HOURS_ONLY == True:
        stock_df = stock_df.between_time("9:30", "16:00")

    stock_df.to_csv(f"../data/alpaca/processed/m1/{stock}.csv")
    print(f"Processed {stock}")

# %%
