import datetime
import numpy as np
import pandas as pd
import queue

from event import SignalEvent

class Strategy():
    """
    Using the Bars of DataHandler, generate Signal event
    """
    def calculate_signals(self):
        raise NotImplementedError()

class BuyAndHoldStrategy(Strategy):
    def __init__(self, bars, events):
        self.bars = bars #? The DataHandler object, confusing name
        self.symbol_list = self.bars.symbol_list
        self.events = events
    
        self.bought = self._calculate_initial_bought()
    
    def _calculate_initial_bought(self):
        bought = {}
        for symbol in self.symbol_list:
            bought[symbol] = False
        return bought
    
    def calculate_signals(self, event):
        'Market event -> Signal event'
        if event.type == 'MARKET': #?Can we just use isinstance?
            for symbol in self.symbol_list:
                bars = self.bars.get_latest_bars(symbol)
                if bars is not None and bars != []:
                    if self.bought[symbol] == False:
                        signal = SignalEvent(bars[0][0], bars[0][1], 'LONG')
                        self.events.put(signal)
                        self.bought[symbol] = True
                        