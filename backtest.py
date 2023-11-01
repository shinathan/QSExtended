import datetime
import pprint
import queue
import time


class Backtest:
    def __init__(
        self,
        csv_dir,
        symbol_list,
        initial_capital,
        heartbeat,
        start_date,
        end_date,
        data_handler,
        execution_handler,
        portfolio,
        strategy,
    ):
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start_date = start_date
        self.end_date = end_date
        self.data_handler_cls = data_handler
        self.execution_handler_cls = execution_handler
        self.portfolio_cls = portfolio
        self.strategy_cls = strategy

        self.events = queue.Queue()  # A FIFO queue

        self.signals = 0
        self.orders = 0
        self.fills = 0
        self.num_strats = 1
        self._generate_trading_instances()

    def _generate_trading_instances(self):
        # Create the DataHandler, Strategy, Portfolio and ExecutionHandler objects
        self.data_handler = self.data_handler_cls(
            self.events, self.csv_dir, self.symbol_list, self.start_date, self.end_date
        )
        self.strategy = self.strategy_cls(self.data_handler, self.events)
        self.portfolio = self.portfolio_cls(
            self.data_handler, self.events, self.start_date, self.initial_capital
        )
        self.execution_handler = self.execution_handler_cls(
            self.events, self.data_handler
        )

    def _run_backtest(self):
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
                            self.orders += 1  # ? Idem
                            self.execution_handler.execute_order(event)
                        elif event.type == "FILL":
                            self.fills += 1
                            self.portfolio.update_fill(event)
            time.sleep(self.heartbeat)  # ? Can become out of sync

    def _output_performance(self):
        self.portfolio.create_equity_curve_dataframe()
        print("Creating summary stats...")
        stats = self.portfolio.output_summary_stats()
        print(stats)
        print(f"{self.signals} signals")
        print(f"{self.orders} orders")
        print(f"{self.fills} fills")

    def simulate_trading(self):
        self._run_backtest()
        self._output_performance()
