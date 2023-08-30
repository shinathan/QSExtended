"""



"""


import pandas as pd
from lightweight_charts import Chart

### SETTINGS ###
DATA_PATH = "../data/polygon/"
################

if __name__ == "__main__":
    chart = Chart()

    data = pd.read_csv(
        DATA_PATH + "raw/m1/SPY.csv",
        parse_dates=True,
        index_col="datetime",
        usecols=["datetime", "open", "high", "low", "close", "volume"],
        nrows=5000,
    )

    chart.set(data)
    chart.show(block=True)
