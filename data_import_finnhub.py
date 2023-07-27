import finnhub
import pandas as pd

finnhub_client = finnhub.Client(api_key="X")
twitter_symbols = finnhub_client.symbol_lookup("twitter")
twitter_symbols = twitter_symbols["result"]
twitter_symbols = pd.DataFrame(twitter_symbols)
twitter_symbols  # No delisted TWTR stock
"""
I decided to not use Finnhub, because they do not
have delisted tickers. The (day trading) strategies
that I am interested in are mainly for the volatile
stocks (like Hertz), which have a higher probability
of being delisted.
"""
