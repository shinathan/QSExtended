import finnhub

finnhub_client = finnhub.Client(api_key="X")
symbols = finnhub_client.stock_symbols("US")
"""
I decided to not use Finnhub, because they do not
have delisted tickers. The (day trading) strategies
that I am interested in are mainly for the volatile
stocks (like Hertz), which have a higher probability
of being delisted.
"""
