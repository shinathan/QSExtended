"""
This script has some functions from the notebooks. There are no functions that are not copy-pasted.
"""


from polygon.rest import RESTClient
from datetime import datetime, date, time, timedelta
from pytz import timezone
import pytz
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import mplfinance as mpf
import os

DATA_PATH = "../../../data/polygon/"


def datetime_to_unix(year=None, month=None, date=None, hour=0, minute=0, dt=None):
    """
    Converts a ET datetime to the corresponding Unix msec stamp.
    The input can either be year/month/date or a datetime object.
        Input must be either
            year : int
            month : int
            date : int
            hour : int (optional)
            minute : int (optional)
        Or
            dt : datetime (keyword-only)
    """
    if all(isinstance(value, int) for value in (year, month, date, hour, minute)):
        time_ET = timezone("US/Eastern").localize(
            datetime(year, month, date, hour, minute)
        )
    elif isinstance(dt, datetime):
        time_ET = timezone("US/Eastern").localize(dt)
    else:
        raise Exception("No year/month/date or datetime object specified.")

    return int(time_ET.timestamp() * 1000)


def download_m1_raw_data(ticker, from_, to, path):
    """
    Downloads 1-minute data from Polygon, converts to ET-naive time and store. Includes extended hours.
        ticker : str
        from_ : tuple(year : int, month : int, date : int) or datetime
        to : tuple(year : int, month : int, date : int) or datetime
        path : str
    """
    # Check if int or datetime given for from_, then get start_unix
    if isinstance(from_, datetime):
        start_unix = datetime_to_unix(dt=from_)
    elif all(isinstance(value, int) for value in from_):
        start_unix = datetime_to_unix(*from_, hour=4)  # (* unpacks the tuple)
    else:
        raise Exception("No year/month/date or datetime object specified.")

    # Check if int or datetime given for to, then get end_unix
    if isinstance(to, datetime):
        end_unix = datetime_to_unix(dt=to)
    elif all(isinstance(value, int) for value in to):
        # Technically the last minute is 19:59 or earlier on early closes, but if we download 20:00 the last bar (or hours for early closes) will simply not exist. So for simplicity we just use hour = 20.
        end_unix = datetime_to_unix(*to, hour=20)  # (* unpacks the tuple)
    else:
        raise Exception("No year/month/date or datetime object specified.")

    with open(DATA_PATH + "secret.txt") as f:
        KEY = next(f).strip()

    client = RESTClient(api_key=KEY)

    m1 = pd.DataFrame(
        client.list_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="minute",
            from_=start_unix,
            to=end_unix,
            limit=10000,
        )
    )
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
    m1.to_csv(path)


def get_trading_days():
    """
    Get a list of trading dates.
    """
    if os.path.isfile(DATA_PATH + "../other/market_hours.csv"):
        trading_hours = pd.read_csv(
            DATA_PATH + "../other/market_hours.csv",
            usecols=["date"],
            index_col="date",
            parse_dates=True,
        )
        return list(trading_hours.index.date)
    else:
        raise Exception("There is no file for market hours.")


def first_trading_day_after(dt):
    """
    Gets first trading day after input date. If there is no file, return the input.
    """
    trading_days = get_trading_days()
    while dt not in trading_days:
        dt = dt + timedelta(days=1)
    return dt


def last_trading_day_before(dt):
    """
    Gets last trading day before input date. If there is no file, return the input.
    """
    trading_days = get_trading_days()
    while dt not in trading_days:
        dt = dt - timedelta(days=1)
    return dt


def get_tickers_v1():
    """
    Retrieves tickers_v1.csv in the correct format.
    """
    tickers_v1 = pd.read_csv(
        DATA_PATH + "raw/tickers_v1.csv",
        parse_dates=True,
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
    tickers_v1["start_date"] = pd.to_datetime(tickers_v1["start_date"]).dt.date
    tickers_v1["end_date"] = pd.to_datetime(tickers_v1["end_date"]).dt.date
    tickers_v1["last_updated_utc"] = pd.to_datetime(
        tickers_v1["last_updated_utc"]
    ).dt.date
    return tickers_v1


def get_tickers_v2():
    """
    Retrieves tickers_v2.csv in the correct format.
    """
    tickers_v2 = pd.read_csv(
        DATA_PATH + "raw/tickers_v2.csv",
        parse_dates=True,
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
    tickers_v2["start_date"] = pd.to_datetime(tickers_v2["start_date"]).dt.date
    tickers_v2["end_date"] = pd.to_datetime(tickers_v2["end_date"]).dt.date
    tickers_v2["last_updated_utc"] = pd.to_datetime(
        tickers_v2["last_updated_utc"]
    ).dt.date
    return tickers_v2


def get_tickers_v3():
    """
    Retrieves tickers_v3.csv in the correct format.
    """
    tickers_v3 = pd.read_csv(
        DATA_PATH + "raw/tickers_v3.csv",
        parse_dates=True,
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
    tickers_v3["start_date"] = pd.to_datetime(tickers_v3["start_date"]).dt.date
    tickers_v3["end_date"] = pd.to_datetime(tickers_v3["end_date"]).dt.date
    tickers_v3["last_updated_utc"] = pd.to_datetime(
        tickers_v3["last_updated_utc"]
    ).dt.date
    return tickers_v3
