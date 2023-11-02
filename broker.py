import datetime
import queue
from event import FillEvent, OrderEvent


class Broker:
    """Interface for simulating the broker.
    Generates: FillEvents
    Handles: OrderEvents
    """

    def execute_order(self, event):
        raise Exception("This is just an interface! Use the implementation.")


class SimulatedBroker(Broker):
    def __init__(self, events, data_handler):
        self.events = events
        self.data_handler = data_handler

    def calculate_fees(self, price, quantity):
        # This should estimate the broker commission AND the spread.
        # If you have access to PFOF brokers, only the spread is enough.
        # Don't forget slippage if you have a large account.
        commission = max(1, quantity * 0.005)
        spread = price * 0.002
        return round(commission + spread, 2)

    def execute_order(self, event):
        if isinstance(event, OrderEvent):
            current_price = self.data_handler.get_latest_bars(event.symbol, N=1).iloc[
                -1
            ]["close"]
            # TODO: option to get next open instead. That is essentially a 1-bar delay.

            fill_event = FillEvent(
                dt=self.data_handler.current_time,
                symbol=event.symbol,
                side=event.side,
                quantity=event.quantity,
                fill_price=current_price,
                fees=self.calculate_fees(current_price, event.quantity),
            )
            self.events.put(fill_event)
