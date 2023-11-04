import datetime
import pprint
import queue
import time
from event import (
    MarketEvent,
    MarketOpenEvent,
    MarketCloseEvent,
    FillEvent,
    OrderEvent,
    BacktestEndEvent,
)


class Backtest:
    def __init__(
        self,
        initial_capital,
        start_date,
        end_date,
        extended_hours,
        strategy,
        data_handler,
        broker,
        portfolio,
    ):
        """Initializes the backtest.

        Args:
            initial_capital (float): the starting capital in USD
            start_date (datetime): the start datetime
            end_date (datetime): the end datetime
            extended_hours (bool): whether to include extended hours in the clock
            strategy (Strategy): the custom strategy
            data_handler (DataHandler): the data handler
            broker (Broker): the broker
            portfolio (Portfolio): the portfolio object
        """
        # The parameters of the backtest
        self.initial_capital = initial_capital
        self.start_date = start_date
        self.end_date = end_date
        self.extended_hours = extended_hours

        # The components of the backtester
        self.events = queue.Queue()  # List of events to handle
        self.data_handler = data_handler(
            self.events, self.start_date, self.end_date, extended_hours
        )
        self.portfolio = portfolio(self.events, self.data_handler, self.start_date)
        self.strategy = strategy(self.events, self.data_handler, self.portfolio)
        self.broker = broker(self.events, self.data_handler)

    def _run_backtest(self):
        while True:
            self.data_handler.next()  # Step one bar

            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if isinstance(event, MarketEvent):
                        self.strategy.calculate_signals()
                    elif isinstance(event, BacktestEndEvent):
                        self.strategy.on_backtest_end()
                    elif isinstance(event, OrderEvent):
                        self.broker.execute_order(event)
                    elif isinstance(event, FillEvent):
                        self.portfolio.update_from_fill(event)
                    elif isinstance(event, MarketCloseEvent):
                        self.strategy.on_market_close()
                        self.portfolio.append_portfolio_log()
                        print(self.data_handler.current_time.isoformat())

            if not self.data_handler.continue_backtest:
                break

    def run(self):
        self._run_backtest()
        self.portfolio.create_df_from_holdings_log().to_csv(
            "output/buy_and_hold_holdings.csv"
        )
        self.portfolio.create_df_from_fills_log().to_csv(
            "output/buy_and_hold_trades.csv"
        )
