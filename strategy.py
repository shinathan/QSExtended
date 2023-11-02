import datetime
import numpy as np
import pandas as pd
import queue

from event import OrderEvent


class Strategy:
    """
    This class defines the trading rules.
    Generates: OrderEvents
    The calculate_signals gets called after a MarketEvent
    """

    def __init__(self, events, data_handler, portfolio, **kwargs):
        self.events = events
        self.data_handler = data_handler
        self.portfolio = portfolio

        # The **kwargs is for strategy parameters. For example the symbol list.

    def calculate_signals(self):
        # Takes the latest market data and creates OrderEvents
        raise NotImplementedError()


class BuyAndHoldStrategy(Strategy):
    # Buy and hold stocks in equal weight

    def __init__(self, events, data_handler, portfolio, symbol_list=["SPY"]):
        self.events = events
        self.data_handler = data_handler  # To retrieve the data
        self.portfolio = portfolio  # To retrieve portfolio stats (equity, cash)

        self.symbol_list = symbol_list

        self.in_market = False

    def on_data(self, event):
        if not self.in_market:
            current_cash = self.portfolio.current_cash
            cash_per_symbol = current_cash / len(self.symbol_list)

            for symbol in self.symbol_list:
                last_close = self.bars.get_latest_bars(symbol, N=1).iloc[-1]["close"]
                stocks_to_buy = int(cash_per_symbol / last_close)  # int = round down
                order = OrderEvent(
                    event.datetime, symbol, side="BUY", quantity=stocks_to_buy
                )
                self.events.put(order)

            self.in_market = True

    def on_backtest_end(self, event):
        # Liquidate everything
        for symbol, position in self.portfolio.current_positions.items():
            order = OrderEvent(event.datetime, symbol, side="SELL", quantity=position)
            self.events.put(order)
