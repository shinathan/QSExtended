class Event:
    """Interface for all Events."""

    pass


class MarketEvent(Event):
    """For when the time period (e.g. 1-minute) has passed. Only the DataHandler generates these."""

    def __init__(self, dt):
        self.datetime = dt


class OnMarketClose(Event):
    """For when the market closes (regular hours close)"""

    pass


class OnMarketOpen(Event):
    """For when the market open (regular hours open)"""

    pass


class OrderEvent(Event):
    """A order to be executed. Only the Portfolio generates these. And only the ExecutionHandler uses them."""

    def __init__(self, dt, symbol, side, quantity, type_="MKT", tif="DAY"):
        self.datetime = dt
        self.symbol = symbol
        self.side = side  # BUY/SELL
        self.quantity = quantity
        self.type = type_  # MKT/LMT (not implemented)
        self.tif = tif  # DAY/GTC/OPG/CLS (not implemented)

        self.direction = 1 if side == "BUY" else -1
        self.print_order()

    def print_order(self):
        print(
            f"{self.datetime.isoformat()} | ORDER {self.side} {self.quantity} of {self.symbol}"
        )


class FillEvent(Event):
    """A filled order. Only the Broker generates these. And only the Portfolio uses them."""

    def __init__(
        self,
        dt,
        symbol,
        side,
        quantity,
        fill,
        commission,
    ):
        self.datetime = dt  # The time of a fill. This may be partial!
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.fill = fill  # The average fill price per share
        self.commission = commission  # The total amount of commission

        self.total_fill = self.fill * self.quantity
        self.total_cost = self.total_fill + self.commission
        self.total_cost_per_share = self.fill + self.commission / self.quantity

        self.direction = 1 if side == "BUY" else -1

    def dict(self):
        return {
            "datetime": self.datetime,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "fill": self.fill,
            "commission": self.commission,
        }
