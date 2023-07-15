import datetime
import pandas as pd
from event import MarketEvent


class DataHandler:
    """
    An interface to:
    -Generate bars
    -Get the last bar ('drip feed')

    """

    def get_latest_bars(self, symbol, N=1):
        """
        returns latest bars
        """
        raise NotImplementedError()

    def update_bars(self):
        """
        returns most recent bar for all symbols
        """
        raise NotImplementedError()


class HistoricCSVDataHandler(DataHandler):
    """
    Read CSVs as if they were provided in live trading
    """

    def __init__(self, events, csv_dir, symbol_list):
        # ?Can be put into ABC and then .super()
        """
        events - The queue
        symbol_list - A list of symbol strings
        """
        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list

        # ?why
        self.symbol_data = {}  # List of dataframes
        self.latest_symbol_data = {}
        self.continue_backtest = True

        self._open_convert_csv_files()


def _open_convert_csv_files(self):
    """
    Using CSV and converting to DataFrames. Assume format is Yahoo, so [Date (YYYY/MM/DD), Open, High, Low, Close, Adj Close, Volume]
    """
    comb_index = None  # ?
    for symbol in self.symbol_list:
        self.symbol_data[symbol] = pd.read_csv(
            f"../data/yahoo/{symbol.upper()}",
            header=0,
            index_col=0,
            parse_dates=True,
            names=["datetime", "open", "high", "low", "close", "adj_close", "volume"],
        )
        self.symbol_data[symbol].sort_index(inplace=True)

        # ?what if market times are not the same. In principle, the cleaned data should not contain empty bars, so this will likely be deleted in the future.

        # Combine indexes of all symbols to get all dates and times that are traded
        if comb_index is None:
            comb_index = self.symbol_data[symbol].index
        else:
            comb_index.union(self.symbol_data[symbol].index)

        self.latest_symbol_data[symbol] = []

    for symbol in self.symbol_list:
        # For the symbols that do not have timestamps that other symbols do, do a forward fill
        self.symbol_data[symbol] = self.symbol_data[symbol].reindex(
            index=comb_index, method="pad"
        )
        self.symbol_data[symbol]["returns"] = (
            self.symbol_data[symbol]["adj_close"].pct_change().dropna()
        )
        self.symbol_data[symbol] = self.symbol_data[
            symbol
        ].iterrows()  # symbol_data now contain iterators

    for symbol in self.symbol_list:
        # ?Why do we have to do this a second time?
        self.symbol_data[symbol] = (
            self.symbol_data[symbol].reindex(index=comb_index, method="pad").iterrows()
        )


def _get_new_bar(self, symbol):
    """
    Returns iterator of
    (symbol, datetime, open, high, low, close, volume)
    """
    for b in self.symbol_data[symbol]:
        yield tuple(
            [
                symbol,
                datetime.datetime.strptime(b[0], "%Y-%m-%d %H:%M:%S"),
                b[1][0],
                b[1][1],
                b[1][2],
                b[1][3],
                b[1][4],
            ]
        )


def get_latest_bars(self, symbol, N=1):
    """
    returns latest N bars
    """
    try:
        bars_list = self.latest_symbol_data[symbol]
    except KeyError:
        print("Symbol does not exist")
    else:
        return bars_list[-N:]


def update_bars(self):
    """
    Put MarketEvent()
    Put latest data in latest_symbol_data
    With real data this would be where a get request is done with the broker API.
    """
    for symbol in self.symbol_list:
        try:
            bar = self._get_new_bar(symbol).next()
        except StopIteration:
            self.continue_backtest = False
        else:
            if bar is not None:
                self.latest_symbol_data[symbol].append(bar)
    self.events.put(MarketEvent())
