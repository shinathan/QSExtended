import datetime
import numpy as np
import pandas as pd
import queue
import performance

from math import floor
from event import FillEvent, OrderEvent


class Portfolio:
    # ?This logic should be delegated to strategy, like in QC
    def update_signal(self, event):
        # SignalEvent -> OrderEvent
        raise NotImplementedError()

    def update_fill(self, event):
        # FillEvent -> update internals
        raise NotImplementedError()


class NaivePortfolio(Portfolio):
    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital

        self.all_positions = (
            self.construct_all_positions()
        )  # Dict of all historic positions ('AAPL', 5)
        self.current_positions = {
            symbol: 0 for symbol in self.symbol_list
        }  # Initialize current positions

        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()

        self.transaction_log = (
            []
        )  # A list, where each entry is a dictionary corresponding to a transaction (things will get incredibly convoluted once partial fills are taken care off...). Only takes fills into account. In the future: If there are multiple fills for one order, they should be grouped by order ID.

    # Initialize is better word
    def construct_all_positions(self):
        d = {symbol: 0 for symbol in self.symbol_list}
        d["datetime"] = self.start_date
        return [d]  # ? A dict with dates is maybe better

    def construct_all_holdings(self):
        d = {symbol: 0 for symbol in self.symbol_list}
        d["datetime"] = self.start_date
        d["cash"] = self.initial_capital
        d["commission"] = 0.0
        d["total"] = self.initial_capital
        return [d]

    # Cant we just get this from all_holdings?
    def construct_current_holdings(self):
        d = {symbol: 0 for symbol in self.symbol_list}
        d["datetime"] = self.start_date
        d["cash"] = self.initial_capital
        d["commission"] = 0.0
        d["total"] = self.initial_capital
        return d

    def update_timeindex(self, event):
        # "MarketEvent -> update logs"
        # current_positions is the only things that stays the same without FillEvents. So that is why we use it to calculate the other stuff.
        latest_datetime = self.bars.get_latest_bar_datetime(self.symbol_list[0])
        # Get current bar
        bars = {}
        for symbol in self.symbol_list:
            bars[symbol] = self.bars.get_latest_bars(symbol)

        # Update positions
        dp = {symbol: 0 for symbol in self.symbol_list}  # Intialize positions
        dp["datetime"] = latest_datetime
        for symbol in self.symbol_list:
            dp[symbol] = self.current_positions[symbol]  # Set positions

        # Append current positions to ALL positions
        self.all_positions.append(dp)

        # Update holdings
        dh = {symbol: 0 for symbol in self.symbol_list}  # Initialize holdings
        dh["datetime"] = latest_datetime
        dh["cash"] = self.current_holdings["cash"]
        dh["commission"] = self.current_holdings["commission"]
        dh["total"] = self.current_holdings["cash"]

        for symbol in self.symbol_list:
            market_value = self.current_positions[
                symbol
            ] * self.bars.get_latest_bar_value(symbol, "close")
            dh[symbol] = market_value
            dh["total"] += market_value

        # Append current holdings to ALL holdings
        self.all_holdings.append(dh)

    def update_positions_from_fill(self, fill):
        # FillEvent -> update current positions
        fill_dir = 0
        if fill.direction == "BUY":
            fill_dir = 1
        elif fill.direction == "SELL":
            fill_dir = -1
        else:
            raise Exception("Incorrect fill direction")

        self.current_positions[fill.symbol] += fill_dir * fill.quantity

    def update_holdings_from_fill(self, fill):
        # FillEvent -> update current holdings
        if fill.direction == "BUY":
            fill_dir = 1
        elif fill.direction == "SELL":
            fill_dir = -1
        else:
            raise Exception("Incorrect fill direction")

        self.current_holdings[fill.symbol] += fill.fill_cost
        self.current_holdings["commission"] += fill.commission
        self.current_holdings["cash"] -= fill.fill_cost + fill.commission
        self.current_holdings["total"] -= fill.fill_cost + fill.commission

    def update_transactions_from_fill(self, fill):
        transaction = {
            "datetime": fill.timeindex,
            "symbol": fill.symbol,
            "price": abs(fill.fill_cost) / fill.quantity,
            "direction": fill.direction,
        }
        self.transaction_log.append(transaction)

    def update_fill(self, event):
        # Does the update holdings and update positions
        if event.type == "FILL":
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)
            self.update_transactions_from_fill(event)

    def generate_naive_order(self, signal):
        # SignalEvent -> OrderEvent
        order = None
        symbol = signal.symbol
        direction = signal.signal_type
        quantity = signal.quantity

        cur_quantity = self.current_positions[symbol]
        order_type = "MKT"

        if direction == "LONG" and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, quantity, "BUY")
        elif direction == "SHORT" and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, quantity, "SELL")
        elif direction == "EXIT" and cur_quantity > 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), "SELL")
        elif direction == "EXIT" and cur_quantity < 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), "BUY")
        return order

    def update_signal(self, event):
        if event.type == "SIGNAL":
            order_event = self.generate_naive_order(event)
            self.events.put(order_event)

    def create_equity_curve_dataframe(self):
        """
        all_holdings is [{h1, h2, ...}] where
        h1 = {AAPL, MSFT, datetime, cash, commission, total}
        """
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index("datetime", inplace=True)
        curve["returns"] = curve["total"].pct_change()
        curve["equity_curve"] = (1.0 + curve["returns"]).cumprod()
        self.equity_curve = curve  # df of datetime: returns, equity_curve

    def output_summary_stats(self):
        total_return = self.equity_curve["equity_curve"][-1]
        returns = self.equity_curve["returns"]
        cum_returns = self.equity_curve["equity_curve"]
        sharpe_ratio = performance.create_sharpe_ratio(returns)
        drawdown, max_dd, dd_duration = performance.create_drawdowns(cum_returns)
        self.equity_curve["drawdown"] = drawdown

        stats = pd.Series(
            [
                f"{round((total_return - 1) * 100, 2)}%",
                round(sharpe_ratio, 2),
                f"{round(max_dd * 100,2)}%",
                dd_duration,
            ],
            index=["Total return", "Sharpe", "Max_DD", "Max_DD_duration"],
        )

        self.equity_curve.to_csv("results.csv")
        performance.plot_results("results.csv")

        # Create transaction log df and save to csv
        transaction_log_df = pd.DataFrame(self.transaction_log)
        transaction_log_df.set_index("datetime", inplace=True)
        transaction_log_df.to_csv("transaction_log.csv")

        return stats
