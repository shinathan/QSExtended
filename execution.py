import datetime
import queue
from event import FillEvent, OrderEvent
from data import HistoricCSVDataHandler


class ExecutionHandler:
    def execute_order(self, event):
        # OrderEvent -> fill -> FillEvent
        raise NotImplementedError()


class SimulatedExecutionHandler(ExecutionHandler):
    def __init__(self, events, bars):
        self.events = events
        self.bars = bars

    def execute_order(self, event):
        if event.type == "ORDER":
            current_price = self.bars.get_latest_bar_value(event.symbol, "close")
            current_time = self.bars.get_latest_bar_datetime(
                self.bars.symbol_list[0]
            )  # Uses first symbol
            if event.direction == "BUY":
                fill_dir = 1
            elif event.direction == "SELL":
                fill_dir = -1

            fill_event = FillEvent(
                current_time,
                event.symbol,
                "SIMU",
                event.quantity,
                event.direction,
                fill_cost=fill_dir * event.quantity * current_price,
            )
            self.events.put(fill_event)
