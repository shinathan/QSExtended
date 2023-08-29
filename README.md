## Progress: By far not completed. Do not use.
**Last update (30 August):** Done with getting a full ticker list. Still a lot of data work to do.

I just started my algotrading journey and am now working on creating a backtester using the QuantStart [tutorial](http://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-I/) and using the [book](http://www.quantstart.com/successful-algorithmic-trading-ebook/). In the process I will learn and improve my Python. The goal is that the backtester can support 1-minute quote data or 1-minute bar data for stocks. I do not care about speed, understanding what happens is the most important. I will (try to) implement the minimum of features that will still make a decent backtester.

The backtester must be able to:
* Backtest on 1-minute OHLCV data (data is always adjusted for everything)
* Backtest on aggregates of data (5m), although the backtester always runs on 1m. This is because we need to track limit/stop orders. In the future I might use higher frequencies, like 15s or 1s at minimum. I will never venture into tick data.
* Handle impartial data (e.g. when a stock is delisted like TWTR)
* Support a dynamic asset universe (e.g. only follow stocks that went +20% the day before; either calculate on the fly or get a list of historical tickers per day. This is necessary for example backtesting gaps. It would be cumbersome to calculate gaps for 3000+ tickers every day. This should be done once, then stored, then used in backtest to refine.)
* Support LMT, STP, MOO and MOC orders.
* Be able to use a small set of descriptive/fundamental data, such as sector and market cap. Mainly used for filtering.
* Trade on the brokerages that I will use. Although I barely have money to trade. Because I am live in the EU, I do not have access to most US brokers. I am therefore directly at a disadvantage because I cannot get zero commissions as PFOF is banned. Also I have to pay for live market data while US brokers always have them for free. Alpaca is the exception.

I do not expect to make money, this is just a fun project to learn algotrading and programming. 

### Short overview of objects in the backtester (the backtester is by far not finished)
* Event queue: queue that stores events like 'market', 'signal', 'order', 'fill'.
* DataHandler: incoming data -> MarketEvent
* Strategy: MarketEvent -> SignalEvent
* Portfolio: SignalEvent -> OrderEvent
* ExecutionHandler ('broker'): OrderEvent -> execution -> FillEvent
