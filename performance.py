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


def fills_to_trades(fills):
    """Converts the fills log to a trade log

    Args:
        fills (DataFrame): the fills log

    Returns:
        DataFrame: the trade log
    """
    trade_log = pd.DataFrame(
        columns=[
            "datetime_in",
            "symbol",
            "side",
            "quantity",
            "entry",
            "exit",
            "datetime_out",
            "fees",
            "net P/L %",
            "net P/L $",
            "remaining_qty",
        ]
    )
    for dt, trade in fills_log.iterrows():
        symbol = trade["symbol"]
        side = trade["side"]
        opposite_side = "SELL" if side == "BUY" else "BUY"
        quantity = trade["quantity"]
        fill_price = trade["fill_price"]
        fees = trade["fees"]

        current_position_in_symbol_opposite = trade_log[
            (trade_log["symbol"] == symbol)
            & (trade_log["side"] == opposite_side)
            & (trade_log["remaining_qty"] > 0)
        ]
        if len(current_position_in_symbol_opposite) == 0:
            # If no open trades in this symbol in the opposite direction, create new trade
            trade_log.loc[len(trade_log)] = [
                dt,
                symbol,
                side,
                quantity,
                fill_price,
                np.nan,
                np.nan,
                fees,
                np.nan,
                np.nan,
                quantity,
            ]
        else:
            # Else we (partially) close the trade(s) and create a new trade if a net position remains. Using FIFO.
            for index, open_trade in current_position_in_symbol_opposite.iterrows():
                remaining_qty_open_trade = open_trade["remaining_qty"]
                already_filled_qty_open_trade = (
                    open_trade["quantity"] - open_trade["remaining_qty"]
                )
                current_average_fill = open_trade["exit"]

                # Partial close of open_trade
                if quantity < remaining_qty_open_trade:
                    if np.isnan(current_average_fill):
                        trade_log.loc[index, "exit"] = fill_price
                    else:
                        average_fill_exit = (
                            (current_average_fill * already_filled_qty_open_trade)
                            + (fill_price * quantity)
                        ) / (
                            already_filled_qty_open_trade + quantity
                        )  # Calculate new average fill
                        trade_log.loc[index, "exit"] = average_fill_exit

                    trade_log.loc[index, "remaining_qty"] -= quantity
                    trade_log.loc[index, "fees"] += fees
                    break  # We don't have to look at the next trade

                # Full close of open_trade
                elif quantity >= remaining_qty_open_trade:
                    if np.isnan(current_average_fill):
                        trade_log.loc[index, "exit"] = fill_price
                    else:
                        average_fill_exit = (
                            (current_average_fill * already_filled_qty_open_trade)
                            + (fill_price * quantity)
                        ) / (
                            already_filled_qty_open_trade + quantity
                        )  # Calculate new average fill
                        trade_log.loc[index, "exit"] = average_fill_exit

                    trade_log.loc[index, "remaining_qty"] = 0
                    trade_log.loc[index, "fees"] += fees
                    trade_log.loc[index, "datetime_out"] = dt

                    if quantity == remaining_qty_open_trade:
                        break  # We don't have to look at the next trade
                    else:
                        quantity = (
                            quantity - remaining_qty_open_trade
                        )  # Calculate remaining quantity

                        # If we are at the end and there is still a remaining quantity, that is a new position
                        if index == len(current_position_in_symbol_opposite) - 1:
                            trade_log.loc[len(trade_log)] = [
                                dt,
                                symbol,
                                side,
                                quantity,
                                fill_price,
                                np.nan,
                                np.nan,
                                fees,
                                np.nan,
                                np.nan,
                                quantity,
                            ]
    return trade_log


def calculate_PNL_trade_log(trade_log):
    """Calculate the PNL for the trade log

    Args:
        trade_log (DataFrame): the trade log

    Returns:
        DataFrame: the trade log with PNL
    """
    trade_log["direction"] = np.where(trade_log["side"] == "BUY", 1, -1)
    trade_log["net P/L %"] = (
        (
            (trade_log["quantity"] - trade_log["remaining_qty"])
            * trade_log["direction"]
            * (trade_log["exit"] - trade_log["entry"])
        )
        - trade_log["fees"]
    ) / trade_log["entry"]
    trade_log["net P/L $"] = (
        (trade_log["quantity"] - trade_log["remaining_qty"]) * trade_log["direction"]
    ) * (trade_log["exit"] - trade_log["entry"]) - trade_log["fees"]
    return trade_log.drop(columns=["direction"])


# Function to get the statistics that use the trade or fill log

# A function that calculates everything, called output_summary(returns, fills)
