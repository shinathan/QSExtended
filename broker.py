import datetime
import queue
from event import FillEvent, OrderEvent


class Broker:
    """Interface for simulating the broker. The broker takes in Order Events and generates Fill Events."""

    def execute_order(self, event):
        raise Exception("This is just an interface! Use the implementation.")


class SimulatedBroker(Broker):
    def __init__(self, events, data_handler):
        self.events = events
        self.data_handler = data_handler

    def calculate_commission(self, price, quantity):
        # This should estimate the broker commissions AND the spread.
        # If you have access to PFOF brokers, only the spread is enough.
        # Don't forget slippage if you have a large account.
        return max(1, quantity * 0.005) + price * 0.002

    def execute_order(self, event):
        if isinstance(event, OrderEvent):
            current_bar = self.data_handler.get_latest_bars(event.symbol, N=1)
            current_price = current_bar["close"].values[
                0
            ]  # TODO: option to get next open instead. That is essentially a 1-bar delay.
            current_time = current_bar.index

            fill_event = FillEvent(
                dt=current_time,
                symbol=event.symbol,
                side=event.side,
                quantity=event.quantity,
                fill_price=current_price,
                commission=self.calculate_commission(current_price, event.quantity),
            )
            self.events.put(fill_event)
