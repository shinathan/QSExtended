class Event:
    pass


class MarketEvent(Event):
    """
    For when new market data arrives from the DataHandler
    """

    def __init__(self):
        self.type = "MARKET"


class SignalEvent(Event):
    """
    The 'advice' generated by the Strategy, which gets passed to Portfolio for risk and order management.
    """

    def __init__(self, symbol, datetime, signal_type, quantity=0):
        """
        symbol - ticker
        datetime - timestamp
        signal_type - either 'LONG' or 'SHORT'
        COMMENT: why no quantity
        """
        self.type = "SIGNAL"
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.quantity = quantity


class OrderEvent(Event):
    """
    The actual order to be executed.
    """

    def __init__(self, symbol, order_type, quantity, direction):
        """
        order_type : 'MKT' or 'LMT'
        direction : 'BUY' or 'SELL'
        """
        self.type = "ORDER"
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction

    def print_order(self):
        print(
            f"Order: {self.order_type} {self.direction} size {self.quantity} of {self.symbol}"
        )


class FillEvent(Event):
    """
    A filled order, sent by the broker/ExecutionHandler
    """

    def __init__(
        self,
        timeindex,
        symbol,
        exchange,
        quantity,
        direction,
        fill_cost,
        commission=None,
    ):
        # bar resolution?
        """
        timeindex : the bar resolution?
        fill_cost : the amount of USD paid
        commission : the commission amount (default is IB)
        """
        self.type = "FILL"
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost

        # This should be generated by the ExecutionHandler and may be removed.
        if commission is None:
            self.commission = self.calculate_ib_commission()
        else:
            self.commission = commission

    def calculate_ib_commission(self):
        return min(self.quantity * 0.005, 1)
