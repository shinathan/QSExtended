## A simplified yet extended version of the OHLC QuantStart backtester

(Work in progress)

This is based on the QuantStart [tutorial](http://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-I/) tutorials and the [book](http://www.quantstart.com/successful-algorithmic-trading-ebook/). The vanilla version had a lot of bugs and didn't even work at all. I have fixed the problems and added some simplifications. For example, I have completely removed SignalEvents. The Strategy now directly sends OrderEvents to the Broker. Also, the Portfolio code is drastically simplified. I also have renamed the ExecutionHandler to Broker. Order and Fills now are more consistent with eachother. And a lot of functions have been renamed and removed unless strictly necessary.

This projects uses the database created here: [here](https://github.com/shinathan/polygon.io-stock-database). However, you can also individually download files and create a new class in DataHandler. Just make sure that there are no time gaps. Use forward fills.

My focus will be on understandability and modularity rather than speed. One should be able to understand all lines of code after following a beginner/intermediate Python course. Then it should be simple to adjust it to your needs. 

### Short overview of objects in the backtester
* DataHandler: generates MarketEvents
* Strategy: MarketEvent -> OrderEvent
* Broker: OrderEvent -> FillEvent
* Portfolio: processes FillEvents, does the administration

The Performance class handles all calculations of the backtest performance. The Backtest class combines all objects to create a backtester. The Strategy defines the trading rules. By instantiating a Backtest with a Strategy, DataHandler, Portfolio and Broker we can run a backtest.
