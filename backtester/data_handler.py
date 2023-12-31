import pandas as pd
import numpy as np

from datetime import date, time
from backtester.event import MarketEvent, MarketCloseEvent, BacktestEndEvent
from polygon.data import get_data
from polygon.times import get_market_minutes, get_market_calendar, get_market_dates


class DataHandler:
    """
    The interface to handle all data needs for live and backtesting.
    The goal is to output OHLC data from the polygon database.

    Generates: MarketEvents
    Handles: None
    """

    def __init__(self, events):
        self.events = events
        # A dictionary of a list of Series containing the most recent data. The reason why it is not a DataFrame is because then we have to build the DataFrame row-by-row. That is extremely slow. And most of the time you only need the last N bars.
        self._latest_bars = {}

    def get_latest_bars(self, symbol, N=1):
        """
        Retrieve the latest bars for a specific symbol from self._latest_bars.
        """
        raise NotImplementedError("This is just an interface! Use the implementation.")

    def next(self):
        """
        Simulates a bar passing.
        Retrieves the latest market data and puts it in self._latest_bars.
        In backtesting this is done with self.all_bars.
        In live trading this is done by an API call or streaming data.
        Then puts a MarketEvent in the queue.
        """
        raise NotImplementedError("This is just an interface! Use the implementation.")


class HistoricalPolygonDataHandler(DataHandler):
    def __init__(self, events, start_date, end_date, timeframe, extended_hours=True):
        self.events = events

        self.timeframe = timeframe
        self._latest_bars = {}  # A FIFO queue with N length may be better
        self._all_bars = {}

        self.current_time = None
        self._time_to_stop = None
        self._clock = self._initiate_clock(start_date, end_date, extended_hours)

        # On the intraday timeframes, we need the market calendar and scheduled events.
        if isinstance(self.timeframe, int):
            self.calendar = get_market_calendar("datetime", self.timeframe)
            # The potential times to check of scheduled events like market close. The reason we check times first is because for some reason this is much faster than checking the datetimes...
            self._potential_scheduled_times = list(np.unique(get_market_calendar("time", self.timeframe)))

        self.continue_backtest = True

    def _initiate_clock(self, start_date, end_date, extended_hours):
        # This is obviously not necessary for live trading.
        """Sets the start and end time and initiates the clock

        Args:
            start_date (Date): the start date
            end_date (Date): the end date
            extended_hours (bool): whether to include extended hours

        Returns:
            generator: the clock generator
        """
        # if self.timeframe is int, that means intraday
        if isinstance(self.timeframe, int):
            market_minutes = get_market_minutes(start_date, end_date, extended_hours, self.timeframe)
        elif self.timeframe == "daily":
            market_minutes = get_market_dates(start_date, end_date)
            market_minutes = pd.to_datetime(market_minutes)

        self.current_time = market_minutes[0]
        self._time_to_stop = market_minutes[-1]

        return self._create_clock(market_minutes)

    def _create_clock(self, market_minutes):
        """A generator that yields the datetime. This simulates a clock."""
        for dt in market_minutes:
            yield dt

    def _check_time(self, timestamp):
        # In live trading this checks the real time with a predefined calendar.
        """Check if a timestamp is a market open/market close

        Args:
            timestamp (datetime): the time to check

        Returns:
            list(Event): a list of scheduled events to process
        """
        scheduled_events = []

        if isinstance(self.timeframe, int):
            # The reason we check times first is because for some reason this is much faster than checking the datetime...
            if timestamp.time() in self._potential_scheduled_times:
                day = timestamp.date()

                # The reason there is no MarketOpenEvent is because the open is always at 9:30 AM. That can be easily included in the Strategy itself.

                if timestamp == self.calendar.loc[day, "regular_close"]:
                    scheduled_events.append(MarketCloseEvent())

                if timestamp == self._time_to_stop:
                    scheduled_events.append(BacktestEndEvent())
        elif self.timeframe == "daily":
            # For daily bars every bar is a market close.
            scheduled_events.append(MarketCloseEvent())
            if timestamp == self._time_to_stop:
                scheduled_events.append(BacktestEndEvent())

        return scheduled_events

    def get_current_market_close_time(self):
        """Gets the market close time

        Returns:
            datetime: the market close time
        """
        return self.calendar.loc[self.current_time.date(), "regular_close"]

    def load_data(
        self,
        symbol,
        start_date=date(2000, 1, 1),
        end_date=date(2100, 1, 1),
        timeframe=1,
        extended_hours=True,
    ):
        # In live trading we either load this from a data vendor or broker.
        """Loads the data. You should build your own 'get_data' function if you use another database. There should be no time gaps!

        Args:
            symbol (str): the ticker or ID
            start (datetime/date, optional): the start date(time) (inclusive). Defaults to no bounds.
            end (datetime/date, optional): the end date(time) (inclusive). Defaults to no bounds.
            timeframe (str, optional): the timeframe of the bar in minutes or 'daily' for daily bars.
            extended_hours (bool, optional): whether we need to keep extended hours. Defaults to True.
        """
        self._latest_bars[symbol] = []

        self._all_bars[symbol] = get_data(
            symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            extended_hours=extended_hours,
        )

    def unload_data(self, symbol):
        """Unloads the data.

        Args:
            symbol (str): the ticker or ID
        """
        self._all_bars.pop(symbol, None)
        self._latest_bars.pop(symbol, None)

    def get_loaded_symbols(self):
        """Get the loaded symbols

        Returns:
            list: list of symbols
        """
        if len(self._all_bars) == 0:
            return list()
        else:
            return list(self._all_bars.keys())

    def next(self):
        """Simulates a passed minute by appending self.latest_bars and generating a MarketEvent.

        Args:
            dt (Datetime): the datetime minute to which we update.
        """
        # Let the clock 'tick'
        self.current_time = next(self._clock)
        if self.current_time == self._time_to_stop:
            self.continue_backtest = False

        # Check if market open/market close.
        # Note: Only the market close/backtest end is necessary because these cannot be easily checked because they are variable. However other scheduled events can be programmed in the Strategy itself easily by checking the current_time.
        scheduled_events = self._check_time(self.current_time)
        for event in scheduled_events:
            self.events.put(event)

        # Update data
        for symbol in self.get_loaded_symbols():
            try:
                # By the way, dictionary lookup is O(1) so we do not need to worry about speed for large dataframes.
                self._latest_bars[symbol].append(self._all_bars[symbol].loc[self.current_time])
            except KeyError:
                print(f"The symbol {symbol} has no data for {self.current_time.isoformat()}.")

        self.events.put(MarketEvent())

    def skip_to_future(self, dt):
        """Sets the clock to a specific time to avoid unnecessary looping. Use with caution. This does not load data.

        Args:
            dt (datetime): the datetime to which to skip to
        """
        while self.current_time < dt:
            self.current_time = next(self._clock)

    def get_latest_bars(self, symbol, N=1):
        """Get the most recent bars

        Args:
            symbol (str): the ticker or ID
            N (int, optional): the amount of bars. Defaults to 1.

        Returns:
            DataFrame: the DataFrame with the data
        """
        return pd.DataFrame(self._latest_bars[symbol][-N:])
