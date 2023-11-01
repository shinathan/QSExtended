"""Most functions were taken from Section 13 from the notebook series."""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from scipy import stats


def calculate_annual_return(returns):
    cum_returns_gross = (returns + 1).cumprod() - 1
    total_length = returns.index[-1] - returns.index[0]
    annual_return = (cum_returns_gross[-1]) ** (1 / (total_length.days / 365)) - 1
    return round(annual_return, 3)


def calculate_sortina(returns, risk_free=0):
    annual_mean = returns.mean() * 252 - risk_free
    annual_downward_std = returns[returns < 0].std() * np.sqrt(252)
    return round(annual_mean / annual_downward_std, 2)


def calculate_sharpe(returns, risk_free=0):
    annual_mean = returns.mean() * 252 - risk_free
    annual_downward_std = returns.std() * np.sqrt(252)
    return round(annual_mean / annual_downward_std, 2)


def calculate_alpha_beta(returns, returns_benchmark, risk_free=0):
    returns = returns - risk_free / 252
    returns_benchmark = returns_benchmark - risk_free / 252
    beta, alpha = stats.linregress(
        returns_benchmark.dropna().values, returns.dropna().values
    )[0:2]
    return round(alpha, 2), round(beta, 2)


def calculate_alpha_beta_weekly(returns, returns_benchmark, risk_free=0):
    returns = returns - risk_free / 52
    returns = returns.resample("1W").last()

    returns_benchmark = returns_benchmark - risk_free / 52
    returns_benchmark = returns_benchmark.resample("1W").last()

    beta, alpha = stats.linregress(
        returns_benchmark.dropna().values, returns.dropna().values
    )[0:2]
    return round(alpha, 2), round(beta, 2)


def calculate_drawdowns(returns):
    """
    Get drawdown Series, maximum DD and maximum duration
    """
    cum_returns = (returns + 1).cumprod() - 1
    cum_returns_gross = cum_returns + 1
    maximum_gross_return = cum_returns_gross.cummax()
    drawdown = 1 - cum_returns_gross / maximum_gross_return

    ATH_series = drawdown[drawdown == 0]
    durations = (
        ATH_series.index[1:].to_pydatetime() - ATH_series.index[:-1].to_pydatetime()
    )

    return -drawdown, round(-drawdown.max(), 3), durations.max()


def plot_fig(daily):
    fig, (ax1, ax2, ax3) = plt.subplots(
        nrows=3, gridspec_kw={"height_ratios": [2, 1, 1]}
    )
    fig.suptitle("IBS", fontsize=16)
    fig.tight_layout(pad=1.5)

    # Returns
    ax1.plot(
        daily.index,
        daily["strategy_cumulative_return"] * 100,
        color="midnightblue",
        linewidth=1,
    )
    ax1.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax1.set_title("Total return", fontsize=10, fontweight="bold")

    # Drawdown
    drawdowns, max_dd, max_dd_duration = calculate_drawdowns(daily["strategy_return"])
    ax2.plot(drawdowns.index, drawdowns * 100, color="firebrick", linewidth=1)
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax2.set_title("Drawdown", fontsize=10, fontweight="bold")

    # Monthly returns
    monthly_return = daily["strategy_return"].resample("1M").sum()
    colors = ["firebrick" if ret < 0 else "g" for ret in monthly_return]
    monthly_return_index = monthly_return.index.values
    monthly_return_index[0] = daily.index[0]  # To make the x-axis align
    monthly_return_index[-1] = daily.index[-1]  # To make the x-axis align

    ax3.bar(monthly_return.index, monthly_return.values * 100, width=15, color=colors)
    ax3.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax3.set_title("Monthly returns", fontsize=10, fontweight="bold")

    plt.show()
