import numpy as np

def calculate_volatility(ticker, prices, liquidity, elapsed_time, current_tender_size, total_time=600):
    """
    Calculates volatility for liability trading based on random-walk prices, liquidity, and current tender size.
    Only used for tender offers involving tickers ABC or XYZ.

    Args:
        ticker (str): Ticker symbol of the security (e.g., 'ABC', 'XYZ').
        prices (list): List of price data points for the ticker.
        liquidity (float): Current liquidity for the ticker (shares available per second).
        elapsed_time (int): Time elapsed in the heat (seconds).
        current_tender_size (int): Size of the current tender offer (shares).
        total_time (int): Total heat time (default 600 seconds).

    Returns:
        float: Adjusted volatility, or None if the ticker is not ABC or XYZ.
    """
    # Validate ticker
    if ticker.upper() not in ["ABC", "XYZ"]:
        print(f"Volatility calculation skipped: Ticker {ticker} not supported.")
        return None  # Skip calculation for unsupported tickers

    # Validate input data
    if len(prices) < 2:
        print(f"Insufficient price data for ticker {ticker}. Using default volatility.")
        return 0.05 # Default medium-high volatility for insufficient data

    if liquidity <= 0:
        raise ValueError(f"Liquidity must be positive for ticker {ticker}.")
    if elapsed_time < 0 or elapsed_time > total_time:
        raise ValueError(f"Elapsed time must be within the range 0 to {total_time} seconds.")

    # Calculate raw returns
    returns = np.diff(prices) / prices[:-1]

    # Compute baseline volatility
    baseline_volatility = np.std(returns)

    # Adjust for tender impact
    tender_impact = current_tender_size / (liquidity + 1)  # Prevent division by zero
    adjusted_volatility = baseline_volatility + tender_impact

    # Apply time-decay factor
    time_decay = 1 - (elapsed_time / total_time)
    time_adjusted_volatility = adjusted_volatility * time_decay

    print(f"Calculated volatility for {ticker}: {time_adjusted_volatility:.4f}")
    return time_adjusted_volatility
