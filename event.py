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
        self.quantity = quantity  # Always positive.
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
        fill_price,
        fees,
    ):
        self.datetime = dt  # The time of a fill. This may be partial!
        self.symbol = symbol
        self.side = side
        self.quantity = quantity  # Always positive.
        self.fill_price = fill_price  # Always positive. Per share.
        self.fees = (
            fees  # The total amount of fees. A positive amount means we pay fees.
        )

        self.total_fill = self.fill_price * self.quantity
        self.total_cost = self.total_fill + self.fees
        self.total_cost_per_share = self.fill_price + self.fees / self.quantity

        self.direction = 1 if side == "BUY" else -1

    def dict(self):
        return {
            "datetime": self.datetime,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "fill_price": self.fill_price,
            "fees": self.fees,
        }
