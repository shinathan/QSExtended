from datetime import datetime
import statsmodels.api as sm

from strategy import Strategy
from event import SignalEvent
from backtest import Backtest
from data import HistoricCSVDataHandler
from portfolio import NaivePortfolio
from execution import SimulatedExecutionHandler
import performance


class PairsStrategy(Strategy):
    def __init__(self, bars, events, ols_window=100, zscore_low=0.5, zscore_high=3.0):
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.ols_window = ols_window
        self.zscore_low = zscore_low
        self.zscore_high = zscore_high

        self.pair = ("AREX", "WLL")
        self.datetime = datetime.utcnow()

        self.long_market = False
        self.short_market = False

    def calculate_xy_signals(self, zscore_last):
        y_signal = None
        x_signal = None
        p0 = self.pair[0]
        p1 = self.pair[1]
        cur_dt = self.datetime
        hedge_ratio = abs(self.hedge_ratio)

        if (
            zscore_last <= -self.zscore_high and not self.long_market
        ):  # Long market means long AREX, short WLL
            self.long_market = True
            y_signal = SignalEvent(p0, cur_dt, "LONG", 10000)
            x_signal = SignalEvent(p1, cur_dt, "SHORT", hedge_ratio * 10000)
        elif abs(zscore_last) <= self.zscore_low and self.long_market:
            self.long_market = False
            y_signal = SignalEvent(p0, cur_dt, "EXIT")
            x_signal = SignalEvent(p1, cur_dt, "EXIT")
        elif zscore_last >= self.zscore_high and not self.short_market:
            self.short_market = True
            y_signal = SignalEvent(p0, cur_dt, "SHORT", 10000)
            x_signal = SignalEvent(p1, cur_dt, "EXIT", hedge_ratio * 10000)
        elif abs(zscore_last) <= self.zscore_low and self.short_market:
            self.short_market = False
            y_signal = SignalEvent(p0, cur_dt, "EXIT")
            x_signal = SignalEvent(p1, cur_dt, "EXIT")

        return y_signal, x_signal

    def calculate_signals_for_pairs(self):
        y = self.bars.get_latest_bars_values(
            self.pair[0], "adj_close", N=self.ols_window
        )
        x = self.bars.get_latest_bars_values(
            self.pair[1], "adj_close", N=self.ols_window
        )
        if y is not None and x is not None:
            if len(y) >= self.ols_window and len(x) >= self.ols_window:
                self.hedge_ratio = sm.OLS(y, x).fit().params[0]
                spread = y - self.hedge_ratio * x
                zscore_last = ((spread - spread.mean()) / spread.std())[-1]
                # We need a simple way to log values later

                y_signal, x_signal = self.calculate_xy_signals(zscore_last)
                if y_signal is not None and x_signal is not None:
                    self.events.put(y_signal)
                    self.events.put(x_signal)

    def calculate_signals(self, event):
        if event.type == "MARKET":
            self.calculate_signals_for_pairs()


backtest = Backtest(
    csv_dir="../data/yahoo",
    symbol_list=["AREX", "WLL"],
    initial_capital=100000,
    heartbeat=0.0,
    start_date=datetime(2017, 1, 1),
    end_date=datetime(2017, 12, 31),
    data_handler=HistoricCSVDataHandler,
    execution_handler=SimulatedExecutionHandler,
    portfolio=NaivePortfolio,
    strategy=PairsStrategy,
)
backtest.simulate_trading()
performance.plot_results("results.csv")
