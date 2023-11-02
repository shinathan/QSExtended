import pandas as pd

from datetime import date, time
from event import MarketEvent, MarketOpenEvent, MarketCloseEvent, BacktestEndEvent
from polygon.data import get_data
from polygon.times import get_market_minutes, get_market_calendar


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
        raise Exception("This is just an interface! Use the implementation.")

    def update_bars(self):
        """
        Retrieves the latest market data and puts it in self._latest_bars.
        In backtesting this is done with self.all_bars.
        In live trading this is done by an API call or streaming data.
        Then puts a MarketEvent in the queue.
        """
        raise Exception("This is just an interface! Use the implementation.")


class HistoricalPolygonDataHandler(DataHandler):
    def __init__(self, events, start_date, end_date, extended_hours=True):
        self.events = events

        self._latest_bars = {}  # A FIFO queue with N length may be better
        self._all_bars = {}
        self._clock = self._create_clock(start_date, end_date, extended_hours)
        self._time_to_stop = get_market_minutes(start_date, end_date, extended_hours)[
            -1
        ]

        self.continue_backtest = True
        self.current_time = next(self._clock)

    def _create_clock(self, start_date, end_date, extended_hours):
        """A generator that yields the datetime. This simulates a clock.

        Args:
            start_date (Date): the start date
            end_date (Date): the end date
            extended_hours (bool): whether to include extended hours
        """
        for dt in get_market_minutes(start_date, end_date, extended_hours):
            yield dt

    def _check_time(self, timestamp):
        """Check if a timestamp is a market open/market close

        Args:
            timestamp (datetime): the time to check

        Returns:
            list(Event): a list of scheduled events to process
        """
        calendar = get_market_calendar("datetime")
        if timestamp.time() in [
            time(9, 30),
            time(15, 59),
            time(19, 59),
        ]:
            day = timestamp.date()
            scheduled_events = []
            if timestamp == calendar.loc[day, "regular_open"]:
                scheduled_events.append(MarketOpenEvent())
            elif timestamp == calendar.loc[day, "regular_close"]:
                scheduled_events.append(MarketCloseEvent())
            if timestamp == self._time_to_stop:
                scheduled_events.append(BacktestEndEvent())
            return scheduled_events
        else:
            return list()

    def load_data(
        self,
        symbol,
        start_date=date(2000, 1, 1),
        end_date=date(2100, 1, 1),
        timeframe=1,
        extended_hours=True,
    ):
        """Loads the data. You should build your own 'get_data' function if you use another database. There should be no time gaps!

        Args:
            symbol (str): the ticker or ID
            start (datetime/date, optional): the start date(time) (inclusive). Defaults to no bounds.
            end (datetime/date, optional): the end date(time) (inclusive). Defaults to no bounds.
            timeframe (str, optional): 1 for 1-minute, 5 for 5-minute. Defaults to daily bars.
            extended_hours (bool, optional): Whether we need to keep extended hours. Defaults to True.
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
        # Update clock
        self.current_time = next(self._clock)
        if self.current_time == self._time_to_stop:
            self.continue_backtest = False

        # Check if market open/market close.
        scheduled_events = self._check_time(self.current_time)
        for event in scheduled_events:
            self.events.put(event)

        # Update data
        for symbol in self.get_loaded_symbols():
            try:
                self._latest_bars[symbol].append(
                    self._all_bars[symbol].loc[self.current_time]
                )
            except KeyError:
                print(
                    f"The symbol {symbol} has no data for {self.current_time.isoformat()}."
                )

        self.events.put(MarketEvent())

    def get_latest_bars(self, symbol, N=1):
        """Get the most recent bars

        Args:
            symbol (str): the ticker or ID
            N (int, optional): the amount of bars. Defaults to 1.

        Returns:
            DataFrame: the DataFrame with the data
        """
        return pd.DataFrame(self._latest_bars[symbol][-N:])
