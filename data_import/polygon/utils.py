"""
This script has some functions from the notebooks.
"""
from polygon.rest import RESTClient
from datetime import datetime, date, time, timedelta
from pytz import timezone
from functools import lru_cache
import pytz
import pandas as pd
import numpy as np
import os

POLYGON_DATA_PATH = "C:/Users/Nathan/Desktop/Algotrading/Code/data/polygon/"
SHARADAR_DATA_PATH = "C:/Users/Nathan/Desktop/Algotrading/Code/data/sharadar/"


def datetime_to_unix(dt):
    """Converts a ET-naive datetime object to msec timestamp

    Args:
        dt (datetime): datetime to convert

    Returns:
        int: Unix millisecond timestamp
    """

    if isinstance(dt, datetime):
        time_ET = timezone("US/Eastern").localize(dt)
        return int(time_ET.timestamp() * 1000)
    else:
        raise Exception("No datetime object specified.")


def download_m1_raw_data(ticker, from_, to, columns, path, client, to_parquet=False):
    """
    Downloads raw 1-minute data from Polygon, converts to ET-naive time and store to either a
    csv file or Parquet file. Includes extended hours.
        ticker : str
        from_ : datetime or date object
        to : datetime or date object
        columns : list of column names to keep
        path : str, if None is specified, the function returns the df instead.
        to_parquet : bool, if
        client : the RESTClient object
    """
    if all(isinstance(value, date) for value in (from_, to)):
        start_unix = datetime_to_unix(dt=datetime.combine(from_, time(4)))
        end_unix = datetime_to_unix(dt=datetime.combine(to, time(20)))
    elif all(isinstance(value, datetime) for value in (from_, to)):
        start_unix = datetime_to_unix(from_)
        end_unix = datetime_to_unix(to)
    else:
        raise Exception("No datetime or date object specified.")

    m1 = pd.DataFrame(
        client.list_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="minute",
            from_=start_unix,
            to=end_unix,
            limit=50000,
            adjusted=False,
        )
    )
    if not m1.empty:
        m1["timestamp"] = pd.to_datetime(
            m1["timestamp"], unit="ms"
        )  # Convert timestamp to UTC
        m1.rename(columns={"timestamp": "datetime"}, inplace=True)
        m1["datetime"] = m1["datetime"].dt.tz_localize(
            pytz.UTC
        )  # Make UTC aware (in order to convert)
        m1["datetime"] = m1["datetime"].dt.tz_convert("US/Eastern")  # Convert UTC to ET
        m1["datetime"] = m1["datetime"].dt.tz_localize(None)  # Make timezone naive
        m1.set_index("datetime", inplace=True)
        m1 = m1[columns]

        if path is None:
            return m1

        if to_parquet:
            m1.to_parquet(path, engine="pyarrow", compression="brotli")
        else:
            m1.to_csv(path)
    else:
        print(
            f"There is no data for {ticker} from {from_.isoformat()} to {to.isoformat()}"
        )


@lru_cache
def get_market_hours():
    """Retrieves the market hours"""
    market_hours = pd.read_csv(
        POLYGON_DATA_PATH + "../other/market_hours.csv", index_col=0
    )
    market_hours.index = pd.to_datetime(market_hours.index).date
    market_hours.premarket_open = pd.to_datetime(
        market_hours.premarket_open, format="%H:%M:%S"
    ).dt.time
    market_hours.regular_open = pd.to_datetime(
        market_hours.regular_open, format="%H:%M:%S"
    ).dt.time
    market_hours.regular_close = pd.to_datetime(
        market_hours.regular_close, format="%H:%M:%S"
    ).dt.time
    market_hours.postmarket_close = pd.to_datetime(
        market_hours.postmarket_close, format="%H:%M:%S"
    ).dt.time
    return market_hours


@lru_cache
def get_market_minutes():
    trading_datetimes = pd.read_csv(POLYGON_DATA_PATH + "../other/trading_minutes.csv")
    return pd.to_datetime(trading_datetimes["datetime"])


def get_market_dates():
    """
    Get a list of trading dates.
    """
    market_hours = get_market_hours()
    return list(market_hours.index)


def first_trading_date_after_equal(dt):
    """
    Gets first trading day after or equal to input date. Return the input if out of range.
    """
    trading_days = get_market_dates()
    if dt > trading_days[-1]:
        print("Out of range! Returning input.")
        return dt
    while dt not in trading_days:
        dt = dt + timedelta(days=1)
    return dt


def last_trading_date_before_equal(dt):
    """
    Gets last trading day before or equal to input date. Return the input if out of range.
    """
    trading_days = get_market_dates()
    if dt < trading_days[-1]:
        print("Out of range! Returning input.")
        return dt
    while dt not in trading_days:
        dt = dt - timedelta(days=1)
    return dt


def remove_extended_hours(bars):
    """
    Remove extended hours.
    """
    # Remove non-regular trading minutes. Only the post-market hours of early closes remain.
    bars = bars.between_time("9:30", "15:59").copy()

    # Remove early close post-market bars
    market_hours = get_market_hours()
    early_closes = market_hours[market_hours["regular_close"] != time(15, 59)]
    for date_, early_close in early_closes.iterrows():
        bars = bars[
            ~(
                (bars.index > datetime.combine(date_, early_close["regular_close"]))
                & (bars.index <= datetime.combine(date_, time(19, 59)))
            )
        ]

    return bars


def get_tickers(v=5):
    """
    Retrieve the ticker list. Default is 5.
    """
    tickers = pd.read_csv(
        f"../../../data/tickers_v{v}.csv",
        parse_dates=["start_date", "end_date"],
        index_col=0,
        keep_default_na=False,
        na_values=[
            "#N/A",
            "#N/A N/A",
            "#NA",
            "-1.#IND",
            "-1.#QNAN",
            "-NaN",
            "-nan",
            "1.#IND",
            "1.#QNAN",
            "<NA>",
            "N/A",
            "NULL",
            "NaN",
            "None",
            "n/a",
            "nan",
            "null",
        ],
    )
    tickers["start_date"] = pd.to_datetime(tickers["start_date"]).dt.date
    tickers["end_date"] = pd.to_datetime(tickers["end_date"]).dt.date
    if tickers.columns.isin(["start_data", "end_data"]).any():
        tickers["start_data"] = pd.to_datetime(tickers["start_data"]).dt.date
        tickers["end_data"] = pd.to_datetime(tickers["end_data"]).dt.date

    tickers["cik"] = tickers["cik"].apply(
        lambda str: float(str) if len(str) != 0 else np.nan
    )
    return tickers


def get_ticker_changes():
    ticker_changes = pd.read_csv(
        POLYGON_DATA_PATH + "../stockanalysis/ticker_changes.csv", index_col=0
    )
    ticker_changes.index = pd.to_datetime(ticker_changes.index).date
    return ticker_changes
