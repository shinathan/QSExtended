import datetime
import pandas as pd
import numpy as np
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

    def get_latest_bar_datetime(self, symbol):
        """
        Get datetime of last bar
        """
        raise NotImplementedError()

    def get_latest_bars_values(self, symbol, val_type, N=1):
        """
        Returns latest OHL or C
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

    def __init__(self, events, csv_dir, symbol_list, start_date, end_date):
        # ?Can be put into ABC and then .super()
        """
        events - The queue
        symbol_list - A list of symbol strings
        """
        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list

        # ?why
        self.symbol_data = {}  # List of generators
        self.latest_symbol_data = {}
        self.continue_backtest = True

        self.start_date = start_date  # The book left this out! As a result, the start and end date in the strategy do nothing
        self.end_date = end_date

        self._open_convert_csv_files()

    def _open_convert_csv_files(self):
        """
        Using CSV and converting to DataFrames. Assume format is Yahoo, so [Date (YYYY/MM/DD), Open, High, Low, Close, Adj Close, Volume]
        """
        comb_index = None  # ?
        for symbol in self.symbol_list:
            self.symbol_data[symbol] = pd.read_csv(
                f"{self.csv_dir}/{symbol.upper()}.csv",
                header=0,
                index_col=0,
                parse_dates=True,
                names=[
                    "datetime",
                    "open",
                    "high",
                    "low",
                    "close",
                    "adj_close",
                    "volume",
                ],
            )

            # Convert to timezone-naive if timezone aware
            if self.symbol_data[symbol].index.tz is not None:
                self.symbol_data[symbol].set_index(
                    self.symbol_data[symbol].index.tz_convert(None), inplace=True
                )
            self.symbol_data[symbol] = self.symbol_data[symbol][
                (self.symbol_data[symbol].index >= self.start_date)
                & (self.symbol_data[symbol].index <= self.end_date)
            ]
            self.symbol_data[symbol].sort_index(inplace=True)

            # ?what if market times are not the same. In principle, the cleaned data should not contain empty bars, so this will likely be deleted in the future.

            # Combine indexes of all symbols to get all dates and times that are traded
            if comb_index is None:
                comb_index = self.symbol_data[symbol].index
            else:
                comb_index.union(self.symbol_data[symbol].index)

            self.latest_symbol_data[
                symbol
            ] = (
                []
            )  # Maybe a dict of dicts makes more sense, because then you can easily lookup dates if the date is a string

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

    def _get_new_bar(self, symbol):
        # A bar is a TUPLE of (Timestamp, Series), where Series is OHLC
        for bar in self.symbol_data[symbol]:
            yield bar

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

    def get_latest_bar_datetime(self, symbol):
        bars_list = self.latest_symbol_data[symbol]
        return bars_list[-1][0]  # Get datetime of last bar, TimeStamp object

    def get_latest_bar_value(self, symbol, val_type):
        # Get O,H,L or C from latest bar
        bars_list = self.latest_symbol_data[symbol]
        return bars_list[-1][1][val_type]

    def get_latest_bars_values(self, symbol, val_type, N=1):
        # Get O,H,L or C from latest bars
        bars_list = self.get_latest_bars(symbol, N)
        return np.array([bar[1][val_type] for bar in bars_list])

    def update_bars(self):
        """
        Put MarketEvent()
        Put latest data in latest_symbol_data
        With real data this would be where a get request is done with the broker API.
        """
        for symbol in self.symbol_list:
            try:
                bar = next(self._get_new_bar(symbol))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[symbol].append(bar)
        self.events.put(MarketEvent())
