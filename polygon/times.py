"""
This file contains several functions for dealing with dates and times for the market.
They were all made in the notebook series https://github.com/shinathan/polygon.io-stock-database.
"""
from datetime import datetime, date, time, timedelta
from functools import lru_cache
import pandas as pd

POLYGON_DATA_PATH = "../data/polygon/"


@lru_cache
def get_market_calendar(format="time"):
    """Retrieves the market hours

    Args:
        format (string): "time" or "datetime". If datetime, the columns are datetime objects. Else time objects.
    Returns:
        DataFrame: the index contains Date objects and the columns Time objects.
    """
    market_hours = pd.read_csv(
        POLYGON_DATA_PATH + "../market/market_calendar.csv", index_col=0
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
    if format == "time":
        return market_hours

    elif format == "datetime":
        market_hours.premarket_open = pd.to_datetime(
            market_hours.index.astype(str)
            + " "
            + market_hours.premarket_open.astype(str)
        )
        market_hours.regular_open = pd.to_datetime(
            market_hours.index.astype(str) + " " + market_hours.regular_open.astype(str)
        )
        market_hours.regular_close = pd.to_datetime(
            market_hours.index.astype(str)
            + " "
            + market_hours.regular_close.astype(str)
        )
        market_hours.postmarket_close = pd.to_datetime(
            market_hours.index.astype(str)
            + " "
            + market_hours.postmarket_close.astype(str)
        )
        return market_hours
    else:
        raise Exception("Input must be 'time' or 'datetime'!")


def get_market_dates():
    """Get a list of market days from the market calendar

    Returns:
        list: list of Date objects
    """
    market_hours = get_market_calendar()
    return list(market_hours.index)


@lru_cache
def get_market_minutes(start_date, end_date, extended_hours=True):
    """Get a DatetimeIndex of trading minutes

    Args:
        start_date (Date): the start date
        end_date (Date): the end date
        extended_hours (bool, optional): whether to include extended hours. Defaults to True.

    Returns:
        DatetimeIndex: the result
    """
    trading_datetimes = pd.read_parquet(
        POLYGON_DATA_PATH + "../market/trading_minutes.parquet"
    )
    trading_datetimes = pd.to_datetime(trading_datetimes.index)
    # Filter for start to end date
    trading_datetimes = trading_datetimes[
        (trading_datetimes >= datetime.combine(start_date, time(4)))
        & (trading_datetimes <= datetime.combine(end_date, time(19, 59)))
    ]
    if extended_hours:
        return trading_datetimes
    else:
        # If we import this in the first line, we have a circular import error
        from polygon.data import remove_extended_hours

        trading_datetimes = pd.DataFrame(index=trading_datetimes)
        return pd.to_datetime(remove_extended_hours(trading_datetimes).index)


def first_trading_date_after_equal(dt):
    """Gets first trading day after or equal to input date. Return the input if out of range.

    Args:
        dt (Date): Date object to compare. Can be a non-trading date.

    Returns:
        Date: the trading date
    """
    trading_days = get_market_dates()
    if dt < trading_days[0] or dt >= trading_days[-1]:
        print("Out of range! Returning input.")
        return dt
    while dt not in trading_days:
        dt = dt + timedelta(days=1)
    return dt


def last_trading_date_before_equal(dt):
    """Gets last trading day before or equal to input date. Return the input if out of range.

    Args:
        dt (Date): Date object to compare. Can be a non-trading date.

    Returns:
        Date: the trading date
    """
    trading_days = get_market_dates()
    if dt <= trading_days[0] or dt > trading_days[-1]:
        print("Out of range! Returning input.")
        return dt
    while dt not in trading_days:
        dt = dt - timedelta(days=1)
    return dt


def first_trading_date_after(day):
    """Gets first trading date after the specified trading date.

    Args:
        day (date): MUST be a trading date

    Returns:
        date: the next trading date
    """
    trading_days = get_market_dates()
    return trading_days[trading_days.index(day) + 1]


def last_trading_date_before(day):
    """Gets last trading date before the specified trading date.

    Args:
        day (date): MUST be a trading date

    Returns:
        date: the previous trading date
    """
    trading_days = get_market_dates()
    return trading_days[trading_days.index(day) - 1]
