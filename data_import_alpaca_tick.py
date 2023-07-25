"""
Gets tick data and converts them to 1-minute OHLC quote (bid/ask) bars.
"""
# %%
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockQuotesRequest
from datetime import datetime, time
from pytz import timezone

import pandas as pd
import numpy as np

# %% 1. DOWNLOAD TICK DATA & SAVE TO CSV
SYMBOL_LIST = ["TOP", "O", "AMC"]
START_DATE = datetime(2023, 1, 25, 4)  # in ET
END_DATE = datetime(2023, 2, 5, 22)  # in ET

for stock in SYMBOL_LIST:
    with open("alpaca_secret.txt") as f:
        PUBLIC_KEY = next(f).strip()
        PRIVATE_KEY = next(f).strip()

    start_date_naive = START_DATE
    start_date_aware = timezone("US/Eastern").localize(start_date_naive)

    end_date_naive = END_DATE
    end_date_aware = timezone("US/Eastern").localize(end_date_naive)

    stock_client = StockHistoricalDataClient(PUBLIC_KEY, PRIVATE_KEY)

    stock_request = StockQuotesRequest(
        symbol_or_symbols=stock, start=start_date_aware, end=end_date_aware
    )
    ticks = stock_client.get_stock_quotes(stock_request)
    ticks.df.to_csv(f"../data/alpaca/raw/tick/{stock}.csv")
    print(f"Downloaded {stock} tick data")

# %% 2. RESAMPLE FROM CSV (TICK -> 1-MINUTE QUOTES)
SYMBOL_LIST = ["TOP", "O", "AMC"]
for stock in SYMBOL_LIST:
    tick_df = pd.read_csv(
        f"../data/alpaca/raw/tick/{stock}.csv",
        usecols=[
            "timestamp",
            "bid_size",
            "bid_price",
            "ask_price",
            "ask_size",
            "conditions",
        ],
        index_col="timestamp",
        parse_dates=True,
    )
    tick_df.index.names = ["datetime"]
    # Convert to ET-naive
    tick_df.set_index(tick_df.index.tz_convert("US/Eastern"), inplace=True)
    tick_df.set_index(tick_df.index.tz_localize(None), inplace=True)

    """
    Resampling procedure:
        We cannot just use resample and then ohlc, because of halts and other special trading conditions.
        So the bid/ask for the corresponding series are:
            -close: use the last available tick. Since we will be trading on the close prices, if the last available tick condition is not R ('regular trading'), the quote bar becomes untradable.
            -open: the open has no use, it is always equal to the previous close
            -high: get highest value of regular trading
            -low: get lowest value of regular trading
        Steps:
            1. Convert tick_df 'conditions' to 'tradable' if R is in conditions.
            2. Convert bid/asks to np.nan if not tradable.
            3. Resample to ohlc for bid/asks, reindex and fill
    """
    # Step 1
    function = np.vectorize(lambda condition_list: "R" in condition_list)
    tick_df["tradeable"] = function(tick_df["conditions"])
    tick_df.drop(columns=["conditions"], inplace=True)
    # Step 2
    tick_df[
        [
            "bid_size",
            "bid_price",
            "ask_price",
            "ask_size",
        ]
    ] = np.where(
        tick_df[["tradeable"]],
        tick_df[
            [
                "bid_size",
                "bid_price",
                "ask_price",
                "ask_size",
            ]
        ],
        np.nan,
    )
    # Step 3.1
    # Close
    minute_df = tick_df.resample("1Min").last()
    minute_df.rename(
        columns={
            "bid_size": "close_bid_size",
            "bid_price": "close_bid",
            "ask_price": "close_ask",
            "ask_size": "close_ask_size",
        },
        inplace=True,
    )

    """
    Step 3.2: Reindex, because we now have non-trading datetimes
    due to resampling.
    We again will use SPY to determine the trading days.
    """
    all_minutes = []
    SPY_df = pd.read_csv(
        f"../data/alpaca/raw/d1/unadjusted/SPY.csv",
        index_col="datetime",
        parse_dates=True,
    )
    SPY_df.set_index(SPY_df.index.tz_convert("US/Eastern"), inplace=True)
    SPY_df.set_index(SPY_df.index.tz_localize(None), inplace=True)
    dates = np.unique(pd.to_datetime(SPY_df.index).date)
    amount_of_days = len(dates)
    for date in dates:
        for hour in range(4, 20):
            for minute in range(0, 60):
                all_minutes.append(
                    datetime.combine(date, time(hour=hour, minute=minute))
                )
    all_minutes = np.array(all_minutes)
    assert len(all_minutes) == amount_of_days * 16 * 60

    start_datetime = minute_df.index[0]
    end_datetime = minute_df.index[-1]

    stock_minutes = all_minutes[
        (all_minutes >= start_datetime.replace(hour=4, minute=0, second=0))
        & (all_minutes <= end_datetime.replace(hour=20, minute=0, second=0))
    ]

    minute_df = minute_df.reindex(stock_minutes)

    """
    Step 3.3 Forward fill values. The reason we do this before
    the high/low, is because high/low cannot be forward filled.
    For forward filling we want the last available data, which
    in this case is the close of the previous bar. Because due
    to forward filling closes, we can just take the current close.

    The backwards filling is only for the first few values, which
    do not matter.

    If no new tick has come in, bid and asks stay the same.
    """
    minute_df = minute_df.ffill().bfill()
    # Also undo the boolean converting due to resampling.
    minute_df["tradeable"] = minute_df["tradeable"].astype(bool)

    # Step 3.3 High & Low
    high_df = tick_df.resample("1Min").max()[["bid_price", "ask_price"]]
    high_df.rename(
        columns={
            "bid_price": "high_bid",
            "ask_price": "high_ask",
        },
        inplace=True,
    )

    low_df = tick_df.resample("1Min").min()[["bid_price", "ask_price"]]
    low_df.rename(
        columns={
            "bid_price": "low_bid",
            "ask_price": "low_ask",
        },
        inplace=True,
    )
    minute_df = pd.merge(
        left=minute_df, right=low_df, how="left", left_index=True, right_index=True
    )
    minute_df = pd.merge(
        left=minute_df, right=high_df, how="left", left_index=True, right_index=True
    )

    # Fill high/low with close
    minute_df["low_bid"] = minute_df["low_bid"].fillna(minute_df["close_bid"])
    minute_df["low_ask"] = minute_df["low_ask"].fillna(minute_df["close_ask"])
    minute_df["high_bid"] = minute_df["high_bid"].fillna(minute_df["close_bid"])
    minute_df["high_ask"] = minute_df["high_ask"].fillna(minute_df["close_ask"])

    # Save to csv
    minute_df[
        [
            "close_bid_size",
            "close_bid",
            "close_ask",
            "close_ask_size",
            "high_bid",
            "high_ask",
            "low_bid",
            "low_ask",
            "tradeable",
        ]
    ].to_csv(f"../data/alpaca/processed/m1/quotes/{stock}.csv")
    print(f"{stock} | Processed tick data to quotes")

# %%
"""
Finally, merge our processed 1-minute OHLC with the 1-minute quote data. 
This is what gets fed into the backtester. OHLC are used for signals,
while quotes are used for trade fills. So it is ONLY used for execution.

If there is not enough size,
we should give a warning. We do not have L2 data. Except for futures,
but futures are already so liquid that it's not worth the hassle
calculating trade impact.
"""
