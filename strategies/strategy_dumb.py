from datetime import datetime, timedelta
import numpy as np

from strategy import Strategy
from event import SignalEvent
from backtest import Backtest
from data_handler import HistoricCSVDataHandler
from broker import SimulatedExecutionHandler
from portfolio import NaivePortfolio

"""
Buy on 23 March, sell 70 days later.
"""


class MovingAverageCrossStrategy(Strategy):
    # Buy if MA(100) > MA(400), sell if otherwise
    def __init__(self, bars, events):
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events

        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        # OUT if no position in stock
        bought = {}
        for symbol in self.symbol_list:
            bought[symbol] = "OUT"  # can use dict comprehension
        return bought

    def calculate_signals(self, event):
        # MarketEvent -> SignalEvent
        if event.type == "MARKET":
            for symbol in self.symbol_list:
                bar_date = self.bars.get_latest_bar_datetime(symbol)
                if (
                    bar_date.month == 3
                    and bar_date.day >= 23
                    and self.bought[symbol] == "OUT"
                ):
                    signal = SignalEvent(symbol, bar_date, "LONG", quantity=100)
                    self.events.put(signal)
                    self.bought[symbol] = "LONG"
                elif (
                    bar_date.month > (datetime(2000, 3, 27) + timedelta(days=70)).month
                    and bar_date.day > (datetime(2000, 3, 27) + timedelta(days=70)).day
                    and self.bought[symbol] == "LONG"
                ):
                    signal = SignalEvent(symbol, bar_date, "EXIT", quantity=100)
                    self.events.put(signal)
                    self.bought[symbol] = "OUT"


backtest = Backtest(
    csv_dir="../data/yahoo",
    symbol_list=["SPY"],
    initial_capital=100000,
    heartbeat=0.0,
    start_date=datetime(2005, 1, 1),
    end_date=datetime(2022, 12, 31),
    data_handler=HistoricCSVDataHandler,
    execution_handler=SimulatedExecutionHandler,
    portfolio=NaivePortfolio,
    strategy=MovingAverageCrossStrategy,
)
backtest.simulate_trading()