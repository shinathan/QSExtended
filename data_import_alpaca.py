"""
Gets 1 minute bars from Alpaca for a list of symbols, between market hours, then converts them to my preferred format. I want to have the following columns: [datetime, open, high, low, close, open_bid, open_ask, high_bid, high_ask, low_bid, low_ask, close_bid, close_ask, close_bid_size, close_ask_size, close_original, volume, tradeable, adjustment]. If some data is unavailable, the value is set to None. However, all stock formats should follow this standard.

1. Download raw adjusted data (m1) from Alpaca and save
2. Open saved raw data, convert them to ["open", "high", "low", "close", "volume", "tradeable"] with ET time and make sure there are no empty rows.
3. Download raw unadjusted and adjusted data (d1) from Alpaca and save.
4. Calculate adjustment factor, add [close_original, adjustment] to processed data

"""
# %%
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import Adjustment

from datetime import datetime, time, timedelta
import pandas as pd
import numpy as np

# %% 1. DOWNLOAD M1 DATA FROM ALPACA AND SAVE TO CSV

### SETTINGS ###
SYMBOL_LIST = ["SPY", "AAPL", "AMC", "GLD", "GME", "O", "SLV", "TLT", "WAL"]
START_DATE = datetime(2020, 1, 1)  # datetime(2015, 12, 1) is start
END_DATE = datetime(2023, 7, 23)
################

with open("alpaca_secret.txt") as f:
    PUBLIC_KEY = next(f).strip()
    PRIVATE_KEY = next(f).strip()

stock_client = StockHistoricalDataClient(PUBLIC_KEY, PRIVATE_KEY)

for stock in SYMBOL_LIST:
    stock_request = StockBarsRequest(
        symbol_or_symbols=stock,
        start=START_DATE,
        end=END_DATE,
        timeframe=TimeFrame(1, TimeFrameUnit.Minute),
        adjustment=Adjustment.ALL,
    )
    bars = stock_client.get_stock_bars(stock_request).df

    stock_df = bars.loc[stock][["open", "high", "low", "close", "volume"]]
    stock_df.index.names = ["datetime"]
    stock_df.to_csv(f"../data/alpaca/raw/m1/{stock}.csv")
    print(f"Downloaded {stock} m1 data")

# %% 2. LOAD FROM CSV AND PROCESS
### SETTINGS ###
SYMBOL_LIST = ["SPY", "AAPL", "AMC", "GLD", "GME", "O", "SLV", "TLT", "WAL"]
MARKET_HOURS_ONLY = True
################

# Problem: Some stocks do not have trades for all minutes the market is open. Especially since we source from IEX.
# Solution: Get the market opening days from SPY. Then create a list of all timestamps the market is open (=SPY is open). Then reindex using this list. Then fill missing values.
all_minutes = []
SPY_df = pd.read_csv(
    f"../data/alpaca/raw/m1/SPY.csv",
    index_col="datetime",
    parse_dates=True,
)
print("Loaded SPY")
SPY_df.set_index(SPY_df.index.tz_convert("US/Eastern"), inplace=True)
SPY_df.set_index(SPY_df.index.tz_localize(None), inplace=True)
dates = np.unique(pd.to_datetime(SPY_df.index).date)
amount_of_days = len(dates)
for date in dates:
    for hour in range(4, 20):
        for minute in range(0, 60):
            all_minutes.append(datetime.combine(date, time(hour=hour, minute=minute)))
all_minutes = np.array(all_minutes)
assert len(all_minutes) == amount_of_days * 16 * 60

for stock in SYMBOL_LIST:
    stock_df = pd.read_csv(
        f"../data/alpaca/raw/m1/{stock}.csv",
        index_col="datetime",
        parse_dates=True,
    )
    stock_df["tradeable"] = True

    stock_df.set_index(stock_df.index.tz_convert("US/Eastern"), inplace=True)
    stock_df.set_index(stock_df.index.tz_localize(None), inplace=True)

    # For some stocks we do not have available data for the entirely of the SPY dates. Hence we need to shrink all_minutes to the dates of the corresponding stock.
    start_datetime = stock_df.index[0]
    end_datetime = stock_df.index[-1]

    stock_minutes = all_minutes[
        (all_minutes >= start_datetime.replace(hour=4, minute=0, second=0))
        & (all_minutes <= end_datetime.replace(hour=20, minute=0, second=0))
    ]

    stock_df = stock_df.reindex(stock_minutes)

    # Fill empty values
    stock_df["tradeable"].fillna(False, inplace=True)
    stock_df["volume"].fillna(0, inplace=True)
    stock_df["close"] = stock_df["close"].fillna(method="ffill")

    stock_df["open"] = stock_df["open"].fillna(stock_df["close"])
    stock_df["low"] = stock_df["low"].fillna(stock_df["close"])
    stock_df["high"] = stock_df["high"].fillna(stock_df["close"])

    # Only affects the very start. Else backfill shouldn't be used because of look-ahead bias.
    stock_df["open"] = stock_df["open"].fillna(method="bfill")

    stock_df["close"] = stock_df["close"].fillna(stock_df["open"])
    stock_df["low"] = stock_df["low"].fillna(stock_df["open"])
    stock_df["high"] = stock_df["high"].fillna(stock_df["open"])

    if MARKET_HOURS_ONLY == True:
        stock_df = stock_df.between_time("9:30", "16:00")

    stock_df.to_csv(f"../data/alpaca/processed/m1/{stock}.csv")
    print(f"Processed {stock}")

# %% 3. DOWNLOAD DAILY ADJUSTED AND UNADJUSTED DATA FROM ALPACA AND SAVE
### SETTINGS ###
SYMBOL_LIST = ["SPY", "AAPL", "AMC", "GLD", "GME", "O", "SLV", "TLT", "WAL"]
START_DATE = datetime(2020, 1, 1)  # datetime(2015, 12, 1) is start
END_DATE = datetime(2023, 7, 23)
MARKET_HOURS_ONLY = True
################
# For every day get the adjustment factor. Using this adjustment factor, adjust the close prices to get close_original. Then when I got quote data, do the same thing.

with open("alpaca_secret.txt") as f:
    PUBLIC_KEY = next(f).strip()
    PRIVATE_KEY = next(f).strip()

stock_client = StockHistoricalDataClient(PUBLIC_KEY, PRIVATE_KEY)

for stock in SYMBOL_LIST:
    stock_request = StockBarsRequest(
        symbol_or_symbols=stock,
        start=START_DATE,
        end=END_DATE,
        timeframe=TimeFrame(1, TimeFrameUnit.Day),
        adjustment=Adjustment.RAW,
    )
    bars = stock_client.get_stock_bars(stock_request).df

    stock_df = bars.loc[stock][["close", "volume"]]
    stock_df.index.names = ["datetime"]
    stock_df.to_csv(f"../data/alpaca/raw/d1/unadjusted/{stock}.csv")
    print(f"Downloaded {stock} adjusted")

    stock_request = StockBarsRequest(
        symbol_or_symbols=stock,
        start=START_DATE,
        end=END_DATE,
        timeframe=TimeFrame(1, TimeFrameUnit.Day),
        adjustment=Adjustment.ALL,
    )
    bars = stock_client.get_stock_bars(stock_request).df

    stock_df = bars.loc[stock][["close"]]
    stock_df.index.names = ["datetime"]
    stock_df.to_csv(f"../data/alpaca/raw/d1/adjusted/{stock}.csv")
    print(f"Downloaded {stock} unadjusted")

# %% 4. GET ADJUSTMENT FACTORS AND ADD CLOSE_ORIGINAL AND ADJUSTMENT TO PROCESSED DATA
SYMBOL_LIST = ["SPY", "AAPL", "AMC", "GLD", "GME", "O", "SLV", "TLT", "WAL"]
for stock in SYMBOL_LIST:
    stock_df_unadjusted = pd.read_csv(
        f"../data/alpaca/raw/d1/unadjusted/{stock}.csv",
        index_col="datetime",
        parse_dates=True,
    )
    stock_df_adjusted = pd.read_csv(
        f"../data/alpaca/raw/d1/adjusted/{stock}.csv",
        index_col="datetime",
        parse_dates=True,
    )
    if not stock_df_adjusted.index.equals(stock_df_unadjusted.index):
        raise Exception(
            "The indices in the adjusted and unadjusted DataFrames are not equal."
        )
    # The unadjusted_close * adjustment = adjusted_close
    adjustment = stock_df_adjusted / stock_df_unadjusted
    adjustment.index = adjustment.index.date
    adjustment.rename(columns={"close": "adjustment"}, inplace=True)

    # In the processed data (step 2), everything is already adjusted.
    stock_df_processed = pd.read_csv(
        f"../data/alpaca/processed/m1/{stock}.csv",
        index_col="datetime",
        parse_dates=True,
    )

    amount_of_days = len(adjustment.index)
    days_in_processed = np.unique(pd.to_datetime(stock_df_processed.index).date)
    amount_of_days_processed = len(days_in_processed)

    if amount_of_days != amount_of_days_processed:
        print(
            f"{stock} | The difference between the adjustment days and the processed days are:"
        )
        print(np.setdiff1d(days_in_processed, adjustment.index))
        print(np.setdiff1d(adjustment.index, days_in_processed))
        raise Exception(
            f"{stock} | Amount of days in adjustments and processed data is not equal."
        )

    stock_df_processed["temp_date"] = stock_df_processed.index.date
    stock_df_with_adj = pd.merge(
        left=stock_df_processed,
        right=adjustment[["adjustment"]],
        how="left",
        left_on="temp_date",
        right_index=True,
    )
    if stock_df_with_adj.isnull().any().any() == True:
        print(
            f"{stock} | WARNING: dataframe contain null values for adjustments. Will do a forward fill and then a backward fill."
        )
        stock_df_with_adj["adjustment"] = (
            stock_df_with_adj["adjustment"]
            .fillna(method="ffill")
            .fillna(method="bfill")
        )
    stock_df_with_adj["close_original"] = (
        stock_df_with_adj["close"] / stock_df_with_adj["adjustment"]
    )
    stock_df_with_adj = stock_df_with_adj[
        [
            "open",
            "high",
            "low",
            "close",
            "close_original",
            "volume",
            "tradeable",
            "adjustment",
        ]
    ]
    stock_df_with_adj.to_csv(f"../data/alpaca/processed/m1/{stock}.csv")
    print(f"{stock} adjustment added")

# %%
