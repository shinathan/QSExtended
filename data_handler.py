import pandas as pd

from datetime import date
from event import MarketEvent
from polygon.data import get_data


class DataHandler:
    """
    The interface to handle all data needs for live and backtesting.
    The goal is to output OHLC data from the polygon database.
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
    def __init__(self, events):
        self.events = events
        self._latest_bars = {}  # A FIFO queue with N length may be better
        self._all_bars = {}

    def load_data(
        self,
        symbol,
        start=date(2000, 1, 1),
        end=date(2100, 1, 1),
        timeframe=1,
        regular_hours_only=False,
    ):
        """Loads the data. You should build your own 'get_data' function if you use another database. There should be no time gaps!

        Args:
            symbol (str): the ticker or ID
            start (datetime/date, optional): the start date(time) (inclusive). Defaults to no bounds.
            end (datetime/date, optional): the end date(time) (inclusive). Defaults to no bounds.
            timeframe (str, optional): 1 for 1-minute, 5 for 5-minute. Defaults to daily bars.
            regular_hours_only (bool, optional): Whether we need to remove extended hours. Defaults to False.
        """
        self._latest_bars[symbol] = []

        self._all_bars[symbol] = get_data(
            symbol,
            start=start,
            end=end,
            timeframe=timeframe,
            regular_hours_only=regular_hours_only,
        )

    def unload_data(self, symbol):
        """Unloads the data.

        Args:
            symbol (str): the ticker or ID
        """
        self._all_bars.pop(symbol, None)
        self._latest_bars.pop(symbol, None)

    def get_latest_bars(self, symbol, N=1):
        """Get the most recent bars

        Args:
            symbol (str): the ticker or ID
            N (int, optional): the amount of bars. Defaults to 1.

        Returns:
            DataFrame: the DataFrame with the data
        """
        return pd.DataFrame(self._latest_bars[symbol][-N:])

    def get_loaded_symbols(self):
        """Get the loaded symbols

        Returns:
            list: list of symbols
        """
        if len(self._all_bars) == 0:
            return list()
        else:
            return list(self._all_bars.keys())

    def update_bars(self, dt):
        """Simulates a passed minute by appending self.latest_bars and generating a MarketEvent.

        Args:
            dt (Datetime): the datetime minute to which we update.
        """
        for symbol in self.get_loaded_symbols():
            try:
                self._latest_bars[symbol].append(self._all_bars[symbol].loc[dt])
            except KeyError:
                print(f"The symbol {symbol} has no data for {dt.isoformat()}.")

        self.events.put(MarketEvent(dt))
