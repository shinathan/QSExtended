## A simplified yet extended version of the OHLC QuantStart backtester

**(Work in progress)**

This is based on the QuantStart [tutorial](http://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-I/) tutorials and the [book](http://www.quantstart.com/successful-algorithmic-trading-ebook/). The vanilla version had a lot of bugs and didn't even work at all. I have fixed the problems and added some simplifications. 

Simplifications:
* SignalsEvents are removed. The Strategy now directly sends OrderEvents to the Broker.
* Also, the Portfolio code is drastically simplified. There are now 2 groups of values: positions and holdings (USD value). The first always changes with fills while the holdings can be updated when necessary (e.g. end of day).
* ExecutionHandler is named to Broker. 
* Order and Fills now are more consistent with eachother. Quantity is always positive for both.
And a lot of functions have been renamed and removed unless strictly necessary.

Added features
* The backtester works even if there is no data supplied. There is now an independent 'clock'. This means that it is possible to dynamically load/unload data. This is handy if the asset universe is dynamic.
* Scheduled events are now possible. These are MarketOpenEvent, MarketCloseEvent and BacktestEndEvent

To do:
* Make sure the backtester also works on 5-minute and daily data and not just on 1-minute bars.
* Add working limit orders.

This projects uses the database created here: [here](https://github.com/shinathan/polygon.io-stock-database). However, you can also individually download files and create a new class in DataHandler. Just make sure that there are no time gaps. Use forward fills.

My focus will be on understandability and modularity rather than speed. One should be able to understand all lines of code after following a beginner/intermediate Python course. Then it should be simple to adjust it to your needs. It is recommended to follow the QuantStart tutorial. (They actually have two series, one is tick-based and one is OHLC-based. You should follow the old OHLC-based one.)

### Short overview of objects in the backtester
* DataHandler: generates MarketEvents
* Strategy: MarketEvent -> OrderEvent
* Broker: OrderEvent -> FillEvent
* Portfolio: processes FillEvents, does the administration

The Performance class handles all calculations of the backtest performance. The Backtest class combines all objects to create a backtester. The Strategy defines the trading rules. By instantiating a Backtest with a Strategy, DataHandler, Portfolio and Broker we can run a backtest.
