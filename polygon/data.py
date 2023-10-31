"""
This file contains several functions for dealing with getting the data from the database we built.
They were all made in the notebook series https://github.com/shinathan/polygon.io-stock-database.
"""
import pyarrow.parquet as pq
from datetime import datetime, date, time, timedelta
from polygon.tickers import get_id
from polygon.times import get_market_calendar

POLYGON_DATA_PATH = "../data/polygon/"


def remove_extended_hours(bars):
    """
    Remove extended hours.
    """
    # Remove non-regular trading minutes. Only the post-market hours of early closes remain.
    bars = bars.between_time("9:30", "15:59").copy()

    # Remove early close post-market bars
    market_hours = get_market_calendar()
    early_closes = market_hours[market_hours["regular_close"] != time(15, 59)]
    for date_, early_close in early_closes.iterrows():
        bars = bars[
            ~(
                (bars.index > datetime.combine(date_, early_close["regular_close"]))
                & (bars.index <= datetime.combine(date_, time(19, 59)))
            )
        ]

    return bars


def get_data(
    ticker_or_id,
    start=date(2000, 1, 1),
    end=date(2100, 1, 1),
    timeframe="daily",
    regular_hours_only=False,
    location="processed",
    columns=[
        "open",
        "high",
        "low",
        "close",
        "close_original",
        "volume",
        "tradeable",
        "halted",
    ],
):
    """Retrieves the data from our database

    Args:
        ticker_or_id (str): the ticker or ID
        start (datetime/date, optional): the start date(time) (inclusive). Defaults to no bounds.
        end (datetime/date, optional): the end date(time) (inclusive). Defaults to no bounds.
        timeframe (str, optional): 1 for 1-minute, 5 for 5-minute. Defaults to daily bars.
        regular_hours_only (bool, optional): Whether we need to remove extended hours. Defaults to False.
        location (str): 'processed' or 'raw'. Defaults to 'processed'.
        columns (list): list of columns. Defaults to all.

    Returns:
        DataFrame: the output
    """

    # Determine if is ID or ticker
    if ticker_or_id[-1].isnumeric():
        id = ticker_or_id
    else:
        id = get_id(ticker_or_id, timeframe)

    # Read data
    if timeframe in [1, 5]:
        dataset = pq.ParquetDataset(
            POLYGON_DATA_PATH + f"{location}/m{timeframe}/{id}.parquet",
            filters=[("datetime", ">=", start), ("datetime", "<=", end)],
        )
    else:
        dataset = pq.ParquetDataset(
            POLYGON_DATA_PATH + f"{location}/d1/{id}.parquet",
            filters=[
                ("datetime", ">=", start),
                ("datetime", "<", end + timedelta(days=1)),
            ],
        )
    df = dataset.read(columns=["datetime"] + columns).to_pandas()

    # Remove extended hours if necessary
    if regular_hours_only and (timeframe in [1, 5]):
        return remove_extended_hours(df)
    else:
        return df
