## A simplified and extended version of the QuantStart backtester

(Work in progress)

This is based on the QuantStart [tutorial](http://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-I/) tutorials and the [book](http://www.quantstart.com/successful-algorithmic-trading-ebook/). The vanilla version had a lot of bugs and didn't even work at all. I have fixed the problems and added some simplifications. For example, I have completely removed SignalEvents. The Strategy now directly sends OrderEvents to the Broker. Also, the Portfolio code is drastically simplified. I also have renamed the ExecutionHandler to Broker.

This projects uses the database created here: [here](https://github.com/shinathan/polygon.io-stock-database). However, you can also individually download files and create a new class in DataHandler. Just make sure that there are no time gaps. Use forward fills.

My focus will be on understandability rather than speed. But it should have the most basic features like limit and stop orders.

### Short overview of objects in the backtester
* DataHandler: generates MarketEvents
* Strategy: MarketEvent -> OrderEvent
* Portfolio: processes FillEvents, does the administration
* Broker: OrderEvent -> FillEvent

The Performance class handles all calculations. The Backtest class combines all objects to create a backtester. The Strategy defines the trading rules. By instantiating a Backtest with a Strategy, DataHandler, Portfolio and Broker we can run a backtest.
