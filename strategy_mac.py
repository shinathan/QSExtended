from datetime import datetime

import numpy as np

from strategy import Strategy
from event import SignalEvent
from backtest import Backtest
from data import HistoricCSVDataHandler
from execution import SimulatedExecutionHandler
from portfolio import NaivePortfolio


class MovingAverageCrossStrategy(Strategy):
    # Buy if MA(100) > MA(400), sell if otherwise
    def __init__(self, bars, events, short_window=10, long_window=50):
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.short_window = short_window
        self.long_window = long_window

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
                bars = self.bars.get_latest_bars_values(
                    symbol, "close", N=self.long_window
                )
                bar_date = self.bars.get_latest_bar_datetime(symbol)
                if bars is not None and bars != []:
                    short_sma = np.mean(bars[-self.short_window :])
                    long_sma = np.mean(bars[-self.long_window :])

                    if short_sma > long_sma and self.bought[symbol] == "OUT":
                        signal = SignalEvent(symbol, bar_date, "LONG")
                        self.events.put(signal)
                        self.bought[symbol] = "LONG"
                    elif short_sma < long_sma and self.bought[symbol] == "LONG":
                        signal = SignalEvent(symbol, bar_date, "EXIT")
                        self.events.put(signal)
                        self.bought[symbol] = "OUT"


backtest = Backtest(
    csv_dir="../data/yahoo",
    symbol_list=["SPY", "UPRO"],
    initial_capital=100000,
    heartbeat=0.0,
    start_date=datetime(2020, 8, 1),
    data_handler=HistoricCSVDataHandler,
    execution_handler=SimulatedExecutionHandler,
    portfolio=NaivePortfolio,
    strategy=MovingAverageCrossStrategy,
)
backtest.simulate_trading()
