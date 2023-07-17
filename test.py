"""
For testing things. Still need to learn testing in python the correct way.

"""
# %%
import performance
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# %%
symbol_list = ["SPY", "UPRO"]
symbol_data = {}
csv_dir = "../data/yahoo"
for symbol in symbol_list:
    symbol_data[symbol] = pd.read_csv(
        f"{csv_dir}/{symbol.upper()}.csv",
        header=0,
        index_col=0,
        parse_dates=True,
        names=[
            "datetime",
            "open",
            "high",
            "low",
            "close",
            "adj_close",
            "volume",
        ],
    )
    symbol_data[symbol].sort_index(inplace=True)


# %%
def create_lagged_series(symbol, start_date, end_date, lags=5):
    # Obtain stock pricing from AlphaVantage
    adj_start_date = start_date
    ts = symbol_data[symbol]["adj_close"]
    # Create the new lagged DataFrame
    tslag = pd.DataFrame(index=ts.index)
    tslag["Today"] = ts
    143
    # Create the shifted lag series of prior trading period close values
    for i in range(0, lags):
        tslag["Lag%s" % str(i + 1)] = ts.shift(i + 1)
    # Create the returns DataFrame
    tsret = pd.DataFrame(index=tslag.index)
    tsret["Today"] = tslag["Today"].pct_change() * 100.0
    # If any of the values of percentage returns equal zero, set them to
    # a small number (stops issues with QDA model in scikit-learn)
    tsret.loc[tsret["Today"].abs() < 0.0001, ["Today"]] = 0.0001
    # Create the lagged percentage returns columns
    for i in range(0, lags):
        tsret["Lag%s" % str(i + 1)] = tslag["Lag%s" % str(i + 1)].pct_change() * 100.0
    # Create the "Direction" column (+1 or -1) indicating an up/down day
    tsret["Direction"] = np.sign(tsret["Today"])
    tsret = tsret[(tsret.index >= start_date) & (tsret.index <= end_date)]
    return tsret


tsret1 = create_lagged_series("SPY", datetime(2018, 8, 1), datetime(2019, 8, 1))


# %%
def create_lagged_series(symbol, start_date, end_date, lags=5):
    data = symbol_data[symbol][["adj_close"]]
    df_lagged = pd.DataFrame(index=data.index)
    df_lagged["lag_0"] = data["adj_close"].pct_change() * 100
    df_lagged.loc[df_lagged["lag_0"].abs() < 0.0001, ["lag_0"]] = 0.0001
    for i in range(1, lags + 1):
        df_lagged[f"lag_{i}"] = df_lagged["lag_0"].shift(i)
    df_lagged["direction"] = np.sign(df_lagged["lag_0"])
    df_lagged = df_lagged[
        (df_lagged.index >= start_date) & (df_lagged.index <= end_date)
    ]
    return df_lagged


tsret = create_lagged_series("SPY", datetime(2018, 8, 1), datetime(2019, 8, 1))

# %%
