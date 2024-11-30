import numpy as np
def calculate_liquidity(order_book, action):
    """
    Calculate liquidity for a specific action (BUY or SELL) based on the order book.

    Args:
        order_book (dict): Order book data with 'bids' and 'asks', where each is a list of [price, volume].
        action (str): Action associated with the tender ('BUY' or 'SELL').

    Returns:
        float: Calculated liquidity based on the action.
    """
    if action.upper() == "SELL":
        # For a buy tender, use the ask side (selling liquidity)
        # to close this position, we must buy the shares back, which will interact with the ask side
        return sum(ask["quantity"] for ask in order_book.get("asks", []))
    elif action.upper() == "BUY":
        # For a sell tender, use the bid side (buying liquidity)
        # to close this position, we must sell the shares back, which will interact with the bid side
        return sum(bid["quantity"] for bid in order_book.get("bids", []))
    else:
        raise ValueError("Invalid action. Use 'BUY' or 'SELL'.")
    
def estimate_close_out_time(tender_size, order_book, action, max_order_size):
    """
    Estimate the time required to close a position based on tender size,
    liquidity, and maximum order size.

    Args:
        tender_size (int): Size of the tender (number of shares).
        liquidity (float): Market liquidity (shares available per second).
        max_order_size (int): Maximum number of shares allowed per order.

    Returns:
        float: Estimated time to close the position (in seconds).
    """
    liquidity = calculate_liquidity(order_book, action)

    if liquidity <= 0:
        return float("inf")  # Infinite time if no liquidity

    # Number of orders needed
    num_orders = np.ceil(tender_size / max_order_size)

    # Time per order (adjusted by liquidity)
    time_per_order = max_order_size / liquidity

    # Total estimated close-out time
    return num_orders * time_per_order + num_orders

def calculate_close_start_time(estimated_close_time, current_tick):
    """
    Calculate the exact tick (timestamp) to start closing the position.

    Args:
        estimated_close_time (float): Estimated time to close the position (in seconds).
        buffer (float): Safety margin to ensure positions are closed in time.
        current_tick (int): Current timestamp in the trading session (in seconds).

    Returns:
        int: Tick (timestamp) to start closing the position.
    """
    

    buffer = 15 # Safety buffer in seconds
    # Calculate the start tick
    close_start_tick = 600 - estimated_close_time - buffer

    # Ensure the start tick is in the future and within valid bounds
    return int(max(current_tick, max(0, close_start_tick)))
