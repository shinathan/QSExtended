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

        # These 'positions' only change with a FillEvent
        # We need to update these at every fill.
        self.current_cash = initial_capital
        self.current_positions = {}  # {'AAPL': 10, 'NFLX': -5, ...}

        # These 'holdings' continuously change depending on market prices
        # We do not necessarily have to update this every bar, but we can
        self._current_positions_value = 0
        self._current_equity = initial_capital

        # These log the portfolio status and all transactions
        self.portfolio_log = []  # list(dict(date, equity, cash, pos. value, positions))
        self.portfolio_log.append(
            {
                "datetime": start_date,
                "equity": self._current_equity,
                "cash": self.current_cash,
                "positions_value": self._current_positions_value,
                "positions": {},
            }
        )
        self.transaction_log = []  # list(dict(date, symbol, side, qty, fill, comm.))

    def update_from_fill(self, fill):
        # Update cash
        self.current_cash -= fill.direction * fill.quantity

        # Update positions
        if fill.symbol in self.current_positions.keys():
            self.current_positions[fill.symbol] += fill.direction * fill.quantity
        else:
            self.current_positions[fill.symbol] = fill.direction * fill.quantity

        # Log transaction
        self.transaction_log.append(fill.dict())

    def _update_holdings_from_market(self):
        # Update positions
        position_values = {
            symbol: position
            * self.data_handler.get_latest_bars(symbol, N=1)["close"].values[0]
            for (symbol, position) in self.current_positions
        }
        self._current_positions_value = sum(position_values.values())

        # Update equity
        self._current_equity == self.current_cash + self._current_positions_value

    def append_portfolio_log(self, dt):
        # Calculate most recent portfolio status
        self._update_holdings_from_market()

        self.portfolio_log.append(
            {
                "datetime": dt,
                "equity": self._current_equity,
                "cash": self.current_cash,
                "positions_value": self._current_positions_value,
                "positions": self.current_positions,
            }
        )

    @property
    def current_positions_value(self):
        self._update_holdings_from_market()
        return self._current_positions_value

    @property
    def current_equity(self):
        self._update_holdings_from_market()
        return self._current_equity

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

        # TODO: stats
