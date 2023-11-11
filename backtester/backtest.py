import queue
import backtester.performance as performance
from backtester.event import (
    MarketEvent,
    MarketCloseEvent,
    FillEvent,
    OrderEvent,
    BacktestEndEvent,
)


class Backtest:
    def __init__(
        self,
        name,
        initial_capital,
        start_date,
        end_date,
        timeframe,
        extended_hours,
        strategy,
        data_handler,
        broker,
        portfolio,
    ):
        """Initializes the backtest.

        Args:
            name (str): the name of the strategy (for storing results)
            initial_capital (float): the starting capital in USD
            start_date (datetime): the start datetime
            end_date (datetime): the end datetime
            timeframe (int/str): the timeframe in minutes or 'daily'. Defaults to 1.
            extended_hours (bool): whether to include extended hours in the clock
            strategy (Strategy): the custom strategy
            data_handler (DataHandler): the data handler
            broker (Broker): the broker
            portfolio (Portfolio): the portfolio object
        """
        self.name = name

        # The parameters of the backtest
        self.initial_capital = initial_capital
        self.start_date = start_date
        self.end_date = end_date
        self.timeframe = timeframe
        self.extended_hours = extended_hours

        # The components of the backtester
        self.events = queue.Queue()  # List of events to handle
        self.data_handler = data_handler(self.events, self.start_date, self.end_date, self.timeframe, extended_hours)
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
                        # print(self.data_handler.current_time.isoformat())
                        # print(self.portfolio._current_equity)

            if not self.data_handler.continue_backtest:
                break

    def run(self):
        # Run backtest
        self._run_backtest()
        self._process_results()

    def _process_results(self):
        # Retrieve portfolio log and trade log
        portfolio_log = self.portfolio.create_df_from_holdings_log()
        portfolio_log.to_csv(f"output/{self.name}_portfolio_log.csv")
        fills_log = self.portfolio.create_df_from_fills_log()
        fills_log.to_csv(f"output/{self.name}_fills_log.csv")

        # Create trade log from fill log
        trade_log = performance.fills_to_trades(fills_log)
        trade_log.to_csv(f"output/{self.name}_trade_log.csv")

        # Create statistics from portfolio, fills and trade log.
        statistics = {
            "Annual return %": performance.calculate_annual_return(portfolio_log),
            "Sharpe": performance.calculate_sharpe(portfolio_log),
            "Sortina": performance.calculate_sortina(portfolio_log),
            "Winning months %": performance.calculate_winning_months(portfolio_log),
            "Time in market %": performance.calculate_time_in_market(portfolio_log),
            "Average profit %": performance.calculate_average_profit(trade_log),
            "Average duration per trade": f"{performance.calculate_average_trade_duration(trade_log)[0]}d{performance.calculate_average_trade_duration(trade_log)[1]}h{performance.calculate_average_trade_duration(trade_log)[2]}m",
            "Profit factor": performance.calculate_profit_factor(trade_log),
            "Trades/month": performance.calculate_trades_per_month(portfolio_log, trade_log),
            "Annual fees %": performance.calculate_fees_drag(portfolio_log, fills_log),
        }

        print(statistics)

        # Plot
        performance.plot_fig(portfolio_log)
