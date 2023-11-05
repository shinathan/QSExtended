# %%
from datetime import datetime
import pandas as pd
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis as QDA
from strategy import Strategy
from event import SignalEvent
import performance
from backtest import Backtest
from data_handler import HistoricCSVDataHandler
from broker import SimulatedExecutionHandler
from portfolio import Portfolio
import numpy as np
from portfolio import NaivePortfolio


class SPYDailyForecastStrategy(Strategy):
    def __init__(self, bars, events):
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.datetime_now = datetime.utcnow()

        self.model_start_date = datetime(2016, 1, 10)
        self.model_end_date = datetime(2017, 12, 31)
        self.model_start_test_date = datetime(2017, 1, 1)  # ???

        self.long_market = False
        self.short_market = False
        self.bar_index = 0

        self.model = self.create_symbol_forecast_model()

    def calculate_signals(self, event):
        cur_date = self.datetime_now
        if event.type == "MARKET":
            self.bar_index += 1
            if self.bar_index > 5:
                lags = self.bars.get_latest_bars_values("SPY", "returns", N=3)
                lags_series = pd.Series(
                    {"lag_1": lags[1] * 100, "lag_2": lags[2] * 100}
                )
                lags_series = lags_series.values.reshape(1, -1)
                prediction = self.model.predict(lags_series)
                if prediction > 0 and not self.long_market:
                    self.long_market = True
                    signal = SignalEvent("SPY", cur_date, "LONG")
                    self.events.put(signal)
                if prediction < 0 and self.long_market:
                    self.long_market = False
                    signal = SignalEvent("SPY", cur_date, "EXIT")
                    self.events.put(signal)

    def create_symbol_forecast_model(self):
        lagged_returns = self.create_lagged_series(
            "SPY", self.model_start_date, self.model_end_date, lags=5
        )
        X = lagged_returns[["lag_1", "lag_2"]]
        y = lagged_returns["direction"]

        X_train = X[X.index <= self.model_start_test_date]
        y_train = y[y.index <= self.model_start_test_date]
        model = QDA()
        model.fit(X_train.values, y_train.values)
        return model

    def create_lagged_series(self, symbol, start_date, end_date, lags=5):
        data = pd.read_csv(
            f"../data/yahoo/{symbol.upper()}.csv",
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
        data.sort_index(inplace=True)
        data = data["adj_close"]
        df_lagged = pd.DataFrame(index=data.index)
        df_lagged["lag_0"] = data.pct_change() * 100
        df_lagged.loc[df_lagged["lag_0"].abs() < 0.0001, ["lag_0"]] = 0.0001
        for i in range(1, lags + 1):
            df_lagged[f"lag_{i}"] = df_lagged["lag_0"].shift(i)
        df_lagged["direction"] = np.sign(df_lagged["lag_0"])
        df_lagged = df_lagged[
            (df_lagged.index >= start_date) & (df_lagged.index <= end_date)
        ]
        return df_lagged


backtest = Backtest(
    csv_dir="../data/yahoo",
    symbol_list=["SPY"],
    initial_capital=100000,
    heartbeat=0.0,
    start_date=datetime(2017, 1, 3),
    end_date=datetime(2019, 12, 31),
    data_handler=HistoricCSVDataHandler,
    execution_handler=SimulatedExecutionHandler,
    portfolio=NaivePortfolio,
    strategy=SPYDailyForecastStrategy,
)
backtest.simulate_trading()
performance.plot_results("results.csv")
# %%
