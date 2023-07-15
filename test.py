import datetime
import pandas as pd


"""
Using CSV and converting to DataFrames. Assume format is Yahoo, so [Date (YYYY/MM/DD), Open, High, Low, Close, Adj Close, Volume]
"""
symbol_list = ["SPY", "UPRO"]

# ?why
symbol_data = {}  # List of dataframes
latest_symbol_data = {}

comb_index = None  # ?
for symbol in symbol_list:
    symbol_data[symbol] = pd.read_csv(
        f"../data/yahoo/{symbol.upper()}.csv",
        header=0,
        index_col=0,
        parse_dates=True,
        names=["datetime", "open", "high", "low", "close", "adj_close", "volume"],
    )
    symbol_data[symbol].sort_index(inplace=True)

    # ?what if market times are not the same. In principle, the cleaned data should not contain empty bars, so this will likely be deleted in the future.

    # Combine indexes of all symbols to get all dates and times that are traded
    if comb_index is None:
        comb_index = symbol_data[symbol].index
    else:
        comb_index.union(symbol_data[symbol].index)

    latest_symbol_data[symbol] = []

for symbol in symbol_list:
    # For the symbols that do not have timestamps that other symbols do, do a forward fill
    symbol_data[symbol] = symbol_data[symbol].reindex(index=comb_index, method="pad")
    symbol_data[symbol]["returns"] = (
        symbol_data[symbol]["adj_close"].pct_change().dropna()
    )
    symbol_data[symbol] = symbol_data[
        symbol
    ].iterrows()  # symbol_data now contain iterators


def _get_new_bar(symbol):
    print("test")
    # A bar is a TUPLE of (Timestamp, Series), where Series is OHLC
    for bar in symbol_data[symbol]:
        print(bar)


_get_new_bar("SPY")
