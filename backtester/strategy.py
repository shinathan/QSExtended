import datetime
import numpy as np
import pandas as pd
import queue

from backtester.event import OrderEvent


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

        # The **kwargs is for strategy parameters. For example the symbol list or the indicator parameters.

    def calculate_signals(self):
        # Takes the latest market data and creates OrderEvents
        raise NotImplementedError()
