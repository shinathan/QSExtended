## A working version of the Quantstart backtester

This is based on the QuantStart [tutorial](http://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-I/) tutorials and the [book](http://www.quantstart.com/successful-algorithmic-trading-ebook/). The vanilla version had a lot of bugs and didn't even work at all. I have fixed the problems and added some simplifications.

This project is currently on hold, because I am focussing on the data and trying out vectorized backtesting. You can follow the other project [here](https://github.com/shinathan/polygon.io-stock-database).

### Short overview of objects in the backtester
* Event queue: queue that stores events like 'market', 'signal', 'order', 'fill'.
* DataHandler: incoming data -> MarketEvent
* Strategy: MarketEvent -> SignalEvent
* Portfolio: SignalEvent -> OrderEvent
* ExecutionHandler ('broker'): OrderEvent -> execution -> FillEvent
