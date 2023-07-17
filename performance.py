import numpy as np
import pandas as pd


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
    drawdown = maximum_return_series - cum_returns

    ATH_series = drawdown[drawdown == 0]
    durations = (
        ATH_series.index[1:].to_pydatetime() - ATH_series.index[:-1].to_pydatetime()
    )

    return drawdown, drawdown.max(), durations.max()
