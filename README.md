## In progres...
**25 July: Currently working on** getting data and manipulating data to fit my needs. I want 1-minute quote data, but vendors only offer ticks or bars.

I just started my algotrading journey and am now working on creating a backtester using the QuantStart tutorial and learning python. The goal is that the backtester can support 1-minute quote data or 1-minute bar data for stocks. I do not care about speed, understanding what happens is the most important.

The data import utils must be able to:
* Download tick data and convert to 1-minute quotebars. Data must be in ET (naive timestamp) and contain some extra information such as if the stock is tradable or not (e.g. halted). This is essential because I want to focus on high volatility stocks (because of my hypothesis that volatility = opportunity), which will have halts.

The backtester must be able to:
* Backtest on 1-minute OHLCV data (data is always adjusted for everything)
* Backtest on 1-minute quote data (data is always adjusted for everything)
* Backtest on aggregates of data (5m), although the backtester always runs on 1m. This is because we need to track limit/stop orders. In the future I might use higher frequencies, like 15s or 1s at minimum. I will never venture into tick data.
* Know when the market is open and also know holidays
    * There should be a function to get closing time
    * There should be a .csv file containing historical trading days and holidays
* Handle impartial data (e.g. when a stock is delisted like TWTR)
* Support a dynamic asset universe (e.g. only follow stocks that went +20% the day before; either calculate on the fly or get a list of historical tickers per day. This is necessary for example backtesting gaps. It would be cumbersome to calculate gaps for 3000+ tickers every day. This should be done once, then stored, then used in backtest to refine.)
* Support LMT and STP orders
* Be able to use a small set of descriptive/fundamental data, such as sector and market cap. Mainly used for filtering. It is necessary anyways if I want to do futures.
* Trade live on Alpaca and InteractiveBrokers with seamless switching from backtesting.

This is the moment I realize that creating a well-functioning backtester is incredibly convoluted. I do not want feature creep, as that will make the backtester less understandable. It should be able to test any arbitrary strategies that uses 1-minute data on stock-like assets. My database will contain fundamentals and 1m OHLC bars for all stocks and 1m quote bars for stocks of interest (and in the future futures). I hope it fits on my disk.

I do not expect to make money, this is just a fun project to learn algotrading and also python (and SQL for my database).

### Short overview (not up to date)
* Event queue: queue that stores events like 'market', 'signal', 'order', 'fill'.
* DataHandler: incoming data -> MarketEvent
* Strategy: MarketEvent -> SignalEvent
* Portfolio: SignalEvent -> OrderEvent
* ExecutionHandler ('broker'): OrderEvent -> execution -> FillEvent
