"""
This file contains several functions for dealing with dates and times for the market.
They were all made in the notebook series https://github.com/shinathan/polygon.io-stock-database.
"""
from datetime import timedelta
from functools import lru_cache
import pandas as pd

POLYGON_DATA_PATH = "../data/polygon/"


@lru_cache
def get_market_calendar():
    """Retrieves the market hours

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
    return market_hours


def get_market_dates():
    """Get a list of market days from the market calendar

    Returns:
        list: list of Date objects
    """
    market_hours = get_market_calendar()
    return list(market_hours.index)


@lru_cache
def get_market_minutes():
    trading_datetimes = pd.read_csv(POLYGON_DATA_PATH + "../market/trading_minutes.csv")
    return pd.to_datetime(trading_datetimes["datetime"])


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
