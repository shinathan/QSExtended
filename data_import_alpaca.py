# %%
import requests
import pandas as pd

SYMBOL = "AAPL"

with open("alpaca_secret.txt") as f:
    PUBLIC_KEY = next(f).strip()
    PRIVATE_KEY = next(f).strip()

headers = {"APCA-API-KEY-ID": PUBLIC_KEY, "APCA-API-SECRET-KEY": PRIVATE_KEY}

response = requests.get(
    f"https://data.alpaca.markets/v2/stocks/AAPL/bars",
    params={
        "timeframe": "1Day",
        "start": "2023-06-01",
        "end": "2023-07-01",
        "adjustment": "all",
    },
    headers=headers,
)

bars = response.json()["bars"]
# %%
df = pd.DataFrame(bars)
df.rename(
    columns={
        "t": "datetime",
        "o": "open",
        "h": "high",
        "l": "low",
        "c": "close",
        "v": "volume",
    },
    inplace=True,
)
df["datetime"] = pd.to_datetime(df["datetime"])
df.set_index("datetime", inplace=True)
df = df[["open", "high", "low", "close", "volume"]]

# %%
