Event queue: queue that stores events like 'market', 'signal', 'order', 'fill'.
DataHandler: incoming data -> MarketEvent
Strategy: MarketEvent -> SignalEvent
Portfolio: SignalEvent -> OrderEvent
ExecutionHandler ('broker'): OrderEvent -> execution -> FillEvent

(we have SPY and UPRO files from yahoo)
Cleaned data should be:
    -Have no empty bars
    -Have bid and ask prices
    Future:
    -Have a 'HALT' tracker: it is possible to calculate indicators using forward filled data, but you cannot trade the stock if it is halted. Likely need another column for this.

QUESTIONS
-Why doesnt the OrderEvent get quantity. Maybe the Portfolio and Strategy class can be merged for simplicity.