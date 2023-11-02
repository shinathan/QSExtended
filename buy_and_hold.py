from event import OrderEvent
from strategy import Strategy
from backtest import Backtest
from datetime import date
from data_handler import HistoricalPolygonDataHandler
from broker import SimulatedBroker
from portfolio import StandardPortfolio


class BuyAndHoldStrategy(Strategy):
    # Buy and hold stocks in equal weight

    def __init__(self, events, data_handler, portfolio, symbol_list=["SPY"]):
        self.events = events
        self.data_handler = data_handler  # To retrieve the data
        self.portfolio = portfolio  # To retrieve portfolio stats (equity, cash)

        self.symbol_list = symbol_list

        for symbol in self.symbol_list:
            self.data_handler.load_data(
                symbol,
                start_date=date(2023, 8, 1),
                end_date=date(2023, 9, 1),
                timeframe=1,
                extended_hours=False,
            )

        self.in_market = False

    def calculate_signals(self):
        if not self.in_market:
            current_cash = self.portfolio.current_cash
            cash_per_symbol = current_cash / len(self.symbol_list)

            for symbol in self.symbol_list:
                last_close = self.data_handler.get_latest_bars(symbol, N=1).iloc[-1][
                    "close"
                ]
                stocks_to_buy = int(cash_per_symbol / last_close)  # int = round down
                order = OrderEvent(
                    self.data_handler.current_time,
                    symbol,
                    side="BUY",
                    quantity=stocks_to_buy,
                )
                self.events.put(order)

            self.in_market = True

    def on_backtest_end(self):
        # Liquidate everything
        for symbol, position in self.portfolio.current_positions.items():
            order = OrderEvent(
                self.data_handler.current_time, symbol, side="SELL", quantity=position
            )
            self.events.put(order)


backtest = Backtest(
    initial_capital=10000,
    start_date=date(2023, 8, 1),
    end_date=date(2023, 9, 1),
    extended_hours=False,
    strategy=BuyAndHoldStrategy,
    data_handler=HistoricalPolygonDataHandler,
    broker=SimulatedBroker,
    portfolio=StandardPortfolio,
)

backtest.run()
