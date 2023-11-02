import datetime
import pprint
import queue
import time


class Backtest:
    def __init__(
        self,
        initial_capital,
        start_date,
        end_date,
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
            strategy (Strategy): the custom strategy
            data_handler (DataHandler): the data handler
            broker (Broker): the broker
            portfolio (Portfolio): the portfolio object
        """
        # The parameters of the backtest
        self.initial_capital = initial_capital
        self.start_date = start_date
        self.end_date = end_date

        # The components of the backtester
        self.events = queue.Queue()  # List of events to handle
        self.data_handler = data_handler(self.events)
        self.strategy = strategy(self.events, self.data_handler, self.portfolio)
        self.broker = broker(self.events, self.data_handler)
        self.portfolio = portfolio(self.events, self.data_handler, self.start_date)

        self._generate_trading_instances()

    def _run_backtest(self):
        """
        REDESIGN:
        -Instead of a infinite while loop, we loop through a clock. This guarantees that everything is aligned. And handles early closes etc. We must make sure it works with custom timeframes.
        -Question: which component should house the 'clock', and how would it work in live trading?
        -Question: what is the most simple solution?
        -I will also add on_end_of_day, on_market_open, on_market_close, on_backtest_end
        """
        while True:
            if self.data_handler.continue_backtest == True:
                self.data_handler.update_bars()  # Get most 'recent' bar
            else:
                break

            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == "MARKET":
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(
                                event
                            )  # ? May not be necessary at every market data if there is no executional logic
                        elif event.type == "ORDER":
                            self.execution_handler.execute_order(event)
                        elif event.type == "FILL":
                            self.portfolio.update_fill(event)
            time.sleep(self.heartbeat)  # ? Can become out of sync

    def _output_performance(self):
        print("Creating summary stats...")
        stats = self.portfolio.output_summary_stats()
        print(stats)

    def simulate_trading(self):
        self._run_backtest()
        self._output_performance()
