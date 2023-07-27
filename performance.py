import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def create_sharpe_ratio(returns, periods=252):
    """
    Get Sharpe
    returns - Pandas Series with percentage returns per bar
    periods - Amount of periods to get the yearly
    """
    return np.sqrt(periods) * (np.mean(returns)) / np.std(returns)


def create_drawdowns(cum_returns):
    """
    Get drawdown Series, maximum DD and maximum duration
    cum_returns - Returns of strategy from the beginning
    """
    maximum_return_series = cum_returns.cummax()
    drawdown = cum_returns - maximum_return_series

    ATH_series = drawdown[drawdown == 0]
    durations = (
        ATH_series.index[1:].to_pydatetime() - ATH_series.index[:-1].to_pydatetime()
    )

    return drawdown, drawdown.min(), durations.max()


def plot_results(equity_file):
    data = pd.read_csv(
        equity_file, header=0, parse_dates=True, index_col=0
    ).sort_values(by="datetime")
    fig, (ax1, ax2, ax3) = plt.subplots(nrows=3)
    ax1.plot(data.index, data["equity_curve"], color="blue")
    ax1.set_ylabel("Total returns")
    ax1.get_yaxis().set_label_coords(-0.1, 0.5)

    ax2.plot(data.index, data["returns"], color="black")
    ax2.set_ylabel("Returns per day")
    ax2.get_yaxis().set_label_coords(-0.1, 0.5)

    ax3.plot(data.index, data["drawdown"], color="red")
    ax3.set_ylabel("Drawdown")
    ax3.get_yaxis().set_label_coords(-0.1, 0.5)

    fig.tight_layout()
