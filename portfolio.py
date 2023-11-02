from datetime import datetime, time
import pandas as pd


class Portfolio:
    """An interface to simulate a portfolio. The portfolio forwards the orders and keeps track of the administration. In real trading, rest API calls can be used. E.g. for getting the real equity.

    Generates: None
    Handles: FillEvents
    """

    def update_from_fill(self, event):
        # FillEvent -> update internals
        raise NotImplementedError()


class StandardPortfolio(Portfolio):
    def __init__(self, events, data_handler, start_date, initial_capital=10000.0):
        self.events = events
        self.data_handler = data_handler

        # These 'positions' only change with a FillEvent
        # We need to update these at every fill.
        self.current_cash = initial_capital
        self.current_positions = {}  # {'AAPL': 10, 'NFLX': -5, ...}

        # These 'holdings' continuously change depending on market prices
        # We do not necessarily have to update this every bar
        self._current_positions_value = 0
        self._current_equity = initial_capital

        # These log the portfolio status and all transactions
        self.portfolio_log = []  # list(dict(date, equity, cash, pos. value, positions))
        self.portfolio_log.append(
            {
                "datetime": datetime.combine(start_date, time(0)),
                "equity": self._current_equity,
                "cash": self.current_cash,
                "positions_value": self._current_positions_value,
                "positions": {},
            }
        )
        self.fills_log = []  # list(dict(date, symbol, side, qty, fill, comm.))

    def update_from_fill(self, fill):
        # Update cash
        self.current_cash -= fill.fill_price * fill.quantity * fill.direction
        self.current_cash -= fill.fees

        # Update positions
        if fill.symbol in self.current_positions.keys():
            self.current_positions[fill.symbol] += fill.direction * fill.quantity
        else:
            self.current_positions[fill.symbol] = fill.direction * fill.quantity

        # Log transaction
        self.fills_log.append(fill.dict())

    def _update_holdings_from_market(self):
        if len(self.data_handler.get_loaded_symbols()) > 0:
            # Update positions value if we have positions
            position_values = {
                symbol: position
                * (self.data_handler.get_latest_bars(symbol, N=1)["close"].values[0])
                for (symbol, position) in self.current_positions.items()
            }
            self._current_positions_value = sum(position_values.values())
        else:
            self._current_positions_value = 0

        # Update equity
        self._current_equity = self.current_cash + self._current_positions_value

    def append_portfolio_log(self):
        self._update_holdings_from_market()

        self.portfolio_log.append(
            {
                "datetime": self.data_handler.current_time,
                "equity": self._current_equity,
                "cash": self.current_cash,
                "positions_value": self._current_positions_value,
                "positions": self.current_positions.copy(),
            }
        )

    @property
    def current_positions_value(self):
        self._update_holdings_from_market()
        return self._current_positions_value

    @property
    def current_equity(self):
        self._update_holdings_from_market()
        return self._current_equity

    ### These functions should only be executed after the backtest
    def create_df_from_holdings_log(self):
        df = pd.DataFrame(self.portfolio_log)
        df.set_index("datetime", inplace=True)
        df["return"] = df["equity"].pct_change()
        df["return_cum"] = (1.0 + df["return"]).cumprod() - 1
        df = df.fillna(value=0)
        return df

    def create_df_from_fills_log(self):
        df = pd.DataFrame(self.fills_log)
        return df.set_index("datetime")
