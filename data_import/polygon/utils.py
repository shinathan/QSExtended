"""
This script has some functions from the notebooks. There are no functions that are not copy-pasted.
"""


from polygon.rest import RESTClient
from datetime import datetime, date, time, timedelta
from pytz import timezone
import pytz
import pandas as pd
import numpy as np
import os

POLYGON_DATA_PATH = "C:/Users/Nathan/Desktop/Algotrading/Code/data/polygon/"
SHARADAR_DATA_PATH = "C:/Users/Nathan/Desktop/Algotrading/Code/data/sharadar/"


def datetime_to_unix(dt):
    """
    Converts a ET-naive datetime object to msec timestamp.
            dt : datetime (keyword-only)
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
            m1.to_parquet(path, engine="pyarrow")
        else:
            m1.to_csv(path)
    else:
        print(
            f"There is no data for {ticker} from {from_.isoformat()} to {to.isoformat()}"
        )


def get_trading_dates():
    """
    Get a list of trading dates.
    """
    if os.path.isfile(POLYGON_DATA_PATH + "../other/market_hours.csv"):
        trading_hours = pd.read_csv(
            POLYGON_DATA_PATH + "../other/market_hours.csv",
            usecols=["date"],
            index_col="date",
            parse_dates=True,
        )
        return list(trading_hours.index.date)
    else:
        raise Exception("There is no file for market hours.")


def first_trading_date_after_equal(dt):
    """
    Gets first trading day after or equal to input date. Return the input if out of range.
    """
    trading_days = get_trading_dates()
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
    trading_days = get_trading_dates()
    if dt < trading_days[-1]:
        print("Out of range! Returning input.")
        return dt
    while dt not in trading_days:
        dt = dt - timedelta(days=1)
    return dt


def get_tickers(v):
    """
    Retrieve the ticker list.
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
    tickers["cik"] = tickers["cik"].apply(
        lambda str: float(str) if len(str) != 0 else np.nan
    )
    return tickers
