## In progres...
**25 July: Currently working on** getting data and manipulating data to fit my needs. I want 1-minute quote data, but vendors only offer ticks or bars.

I just started my algotrading journey and am now working on creating a backtester using the QuantStart tutorial. The goal is that the backtester can support 1-minute quote data or 1-minute bar data for stocks and futures. I do not care about speed, understanding what happens is the most important.

### Short overview (not up to date)
* Event queue: queue that stores events like 'market', 'signal', 'order', 'fill'.
* DataHandler: incoming data -> MarketEvent
* Strategy: MarketEvent -> SignalEvent
* Portfolio: SignalEvent -> OrderEvent
* ExecutionHandler ('broker'): OrderEvent -> execution -> FillEvent
