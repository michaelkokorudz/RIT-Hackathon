from src.close_out_utils import estimate_close_out_time

def evaluate_tender(tender, market_data, time_remaining, config):
    """
    Evaluates whether to accept or reject a tender offer based on profitability and feasibility.

    Args:
        tender (dict): Details of the tender offer.
        market_data (dict): Market data for the relevant ticker.
        time_remaining (float): Time left in the session.
        config (dict): Configuration parameters for evaluation.

    Returns:
        dict: Evaluation result with decision and reasoning.
    """
    print(f"Evaluating tender: {tender}")
    
    ticker = tender.get("ticker")
    tender_size = tender.get("quantity", 0)
    tender_price = tender.get("price", 0)
    action = tender.get("action", "").upper()

    print(f"Tender details: ticker={ticker}, size={tender_size}, price={tender_price}, action={action}")

    # Extract market data
    market_price = market_data[ticker]["last"]
    bid_price = market_data[ticker]["bid"]
    ask_price = market_data[ticker]["ask"]
    volatility = market_data[ticker]["volatility"]
    liquidity = market_data[ticker]["liquidity"]

    print(f"Market data for {ticker}: last={market_price}, bid={bid_price}, ask={ask_price}, volatility={volatility}, liquidity={liquidity}")

    # Adjust bid/ask prices based on volatility
    adjusted_bid = bid_price - volatility * config["volatility_multiplier"]
    adjusted_ask = ask_price + volatility * config["volatility_multiplier"]

    # Ensure the tender price is competitive
    if action == "SELL":
        # For SELL offers, tender price must be higher than market ask
        if tender_price <= ask_price:
            return {"decision": "REJECT", "reason": "Tender price is not above the market ask price"}
    elif action == "BUY":
        # For BUY offers, tender price must be lower than market bid
        if tender_price >= bid_price:
            return {"decision": "REJECT", "reason": "Tender price is not below the market bid price"}

    # Estimate close-out time
    try:
        estimated_close_time = estimate_close_out_time(
            tender_size,
            order_book=market_data[ticker]["order_book"],
            action=action,
            max_order_size=config["max_order_size"]
        )
        print(f"Estimated close-out time: {estimated_close_time}")
    except Exception as e:
        print(f"Error estimating close-out time: {e}")
        return {"decision": "REJECT", "reason": "Error estimating close-out time"}

    # Feasibility checks
    if estimated_close_time > time_remaining:
        return {"decision": "REJECT", "reason": "Not enough time to close position"}
    if liquidity / tender_size < config["liquidity_to_tender_ratio"]:
        return {"decision": "REJECT", "reason": "Insufficient liquidity"}

    # Profitability calculation
    try:
        profit_per_share = tender_price - adjusted_ask if action == "SELL" else adjusted_bid - tender_price
        total_profit = profit_per_share * tender_size
        print(f"Profit per share: {profit_per_share}, Total profit: {total_profit}")
    except Exception as e:
        print(f"Error calculating profit: {e}")
        return {"decision": "REJECT", "reason": "Error calculating profit"}

    # Decision based on profitability
    return {
        "decision": "ACCEPT" if total_profit > 0 else "REJECT",
        "reason": "Profitable" if total_profit > 0 else "Not profitable",
        "profit": total_profit,
        "estimated_close_time": estimated_close_time,
    }
