"""
TradingView chart

"""
import pandas as pd
from lightweight_charts import Chart

### SETTINGS ###
DATA_PATH = "../data/polygon/"
################

if __name__ == "__main__":
    chart = Chart()

    data = pd.read_csv(
        DATA_PATH + "raw/m1/AXLA.csv",
        parse_dates=True,
        index_col="datetime",
        usecols=["datetime", "open", "high", "low", "close", "volume"],
    )

    chart.set(data)
    chart.show(block=True)
