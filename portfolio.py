import datetime
import numpy as np
import pandas as pd
import queue
from performance import *

from math import floor
from event import FillEvent, OrderEvent


class Portfolio:
    """An interface to simulate a portfolio. The portfolio forwards the orders and keeps track of the administration. In real trading, rest API calls can be used. E.g. for getting the real equity."""

    def update_from_fill(self, event):
        # FillEvent -> update internals
        raise NotImplementedError()


class StandardPortfolio(Portfolio):
    def __init__(self, events, data_handler, start_date, initial_capital=10000.0):
        self.events = events
        self.data_handler = data_handler
        self.start_date = start_date

        self.current_cash = initial_capital
        self.current_positions = {}  # {'AAPL': 10, 'NFLX': -5, ...}
        self.current_positions_value = 0
        self.current_equity = initial_capital

        self.holdings_log = []  # list(dict(date, equity, cash, pos. value, positions))
        self.holdings_log.append(
            {
                "datetime": start_date,
                "equity": self.current_equity,
                "cash": self.current_cash,
                "positions_value": 0,
                "positions": {},
            }
        )
        self.transaction_log = []  # list(dict(date, symbol, side, qty, fill, comm.))

    def update_positions_from_fill(self, fill):
        # Update current positions
        if fill.symbol in self.current_positions.keys():
            self.current_positions[fill.symbol] += fill.direction * fill.quantity
        else:
            self.current_positions[fill.symbol] == fill.direction * fill.quantity

    def update_holdings_from_fill(self, fill):
        # Update the holdings (cash, equity, positions)
        self.current_cash -= fill.direction * fill.quantity
        position_values = {
            symbol: position * self.data_handler.get_latest_bars(symbol, N=1)
            for (symbol, position) in self.current_positions
        }
        self.current_positions_value = sum(position_values.values())
        self.current_equity += fill.direction * fill.quantity

    def append_holdings_log(self, fill):
        self.holdings_log.append(
            {
                "datetime": fill.datetime,
                "equity": self.current_equity,
                "cash": self.current_cash,
                "positions_value": self.current_positions_value,
                "positions": self.current_positions,
            }
        )

    def append_transaction_log(self, fill):
        self.transaction_log.append(fill.dict())

    def update_from_fill(self, fill):
        # Executes the above three functions
        if isinstance(fill, FillEvent):
            self.update_positions_from_fill(fill)
            self.update_holdings_from_fill(fill)

            self.append_holdings_log(fill)
            self.append_transaction_log(fill)

    ### These functions should only be executed after the backtest
    def create_df_from_holdings_log(self):
        df = pd.DataFrame(self.holdings_log)
        df.set_index("datetime", inplace=True)
        df["returns"] = df["total"].pct_change()
        df["returns_cum"] = (1.0 + df["returns"]).cumprod() - 1
        return df

    def output_summary_stats(self):
        df = self.create_df_from_holdings_log(self)
        plot_fig(df)

        # Stats
