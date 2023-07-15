import datetime
import queue
from event import FillEvent, OrderEvent


class ExecutionHandler:
    def execute_order(self, event):
        # OrderEvent -> fill -> FillEvent
        raise NotImplementedError()


class SimulatedExecutionHandler(ExecutionHandler):
    def __init__(self, events):
        self.events = events

    def execute_order(self, event):
        if event.type == "ORDER":
            fill_event = FillEvent(
                datetime.datetime.utcnow(),
                event.symbol,
                "SIMU",
                event.quantity,
                event.direction,
                None,
            )
            self.events.put(fill_event)
