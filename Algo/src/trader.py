from statistics import mean, stdev
from collections import deque
from src.config import TRADING_CONFIG, LOG_CONFIG
import time
from typing import Dict, Any, List
from src.client import RITClient
from src.position_tracker import PositionTracker
from src.config import SecurityConfig
from enum import Enum
import numpy as np

class OrderAction(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"

class Trader:
    def __init__(
        self,
        client: RITClient,
        position_tracker: PositionTracker,
        securities_config: Dict[str, SecurityConfig]
    ):
        self.client = client
        self.position_tracker = position_tracker
        self.securities_config = securities_config
        self.trading_params = TRADING_CONFIG['market_making']
        
        # Initialize price history for each security
        self.price_history = {
            ticker: deque(maxlen=20)  # Keep last 20 prices for basic stats and mean reversion
            for ticker in securities_config.keys()
        }
        
        # Track last update time for order refresh
        self.last_order_time = {ticker: 0 for ticker in securities_config.keys()}
        
        # Initialize logging
        self.trade_count = 0
        
        print("\n=== Trader Initialized ===")
        print(f"Trading parameters:")
        print(f"- Min spread: {self.trading_params.min_spread}")
        print(f"- Target spread: {self.trading_params.target_spread}")
        print(f"- Order refresh time: {self.trading_params.order_refresh_time}s\n")
    #records the mid pricers for each security, which is the average of the bid and ask prices for mean reversion calculations.
    def update_price_history(self, securities: Dict[str, Dict[str, Any]]):
        """Update price history with mid prices"""
        for ticker, security in securities.items():
            if ticker in self.price_history:
                mid_price = (security['bid'] + security['ask']) / 2
                self.price_history[ticker].append(mid_price)
    #computes bid and ask prices based on the market and the position, 
    # artificially inflating the spread based on the position to tell 
    # the algorithm not to trade if the position is too large in that specific security
    def calculate_order_prices(self, security: Dict[str, Any]) -> tuple:
        ticker = security['ticker']
        config = self.securities_config[ticker]
        current_position = self.position_tracker.get_position(ticker)
        
        # Get basic price levels
        mid_price = (security['bid'] + security['ask']) / 2
        spread = max(config.min_spread, self.trading_params.target_spread)
        
        # Adjust spread based on position
        position_limit = config.position_limit
        position_ratio = current_position / position_limit
        spread_adjustment = 1.0 + (abs(position_ratio) * 0.2)  # Max 20% spread adjustment
        
        # Calculate prices
        half_spread = (spread * spread_adjustment) / 2
        bid_price = round(mid_price * (1 - half_spread), 2)
        ask_price = round(mid_price * (1 + half_spread), 2)
        
        return bid_price, ask_price
    #determines the appropriate order size based on the trader's current position relative to position limits.
    def calculate_order_size(self, ticker: str) -> int:
        config = self.securities_config[ticker]
        current_position = self.position_tracker.get_position(ticker)
        base_size = self.trading_params.base_order_size[ticker]
        
        #Adjust size based on current position
        position_ratio = abs(current_position / config.position_limit)
        size_scalar = 1.0 - (position_ratio ** 2)  # Quadratic reduction
        
        # Calculate final size
        size = int(base_size * size_scalar)
        size = max(self.trading_params.min_order_size, size)
        size = min(size, config.max_order_size)
        
        # Round to nearest lot size
        lot_size = 100
        size = (size // lot_size) * lot_size
        
        return size
    #ensures that orders are refreshed at a regular interval to prevent stale orders from being left in the market.
    def should_refresh_orders(self, ticker: str) -> bool:
        current_time = time.time()
        if current_time - self.last_order_time[ticker] >= self.trading_params.order_refresh_time:
            self.last_order_time[ticker] = current_time
            return True
        return False
    #places bid and ask orders dynamically based on market data and the trader’s position.
    def execute_trades(self, security: Dict[str, Any]) -> int:
        ticker = security['ticker']

        # Basic market data check
        current_bid = security.get('bid', 0)
        current_ask = security.get('ask', 0)
        if current_bid <= 0 or current_ask <= 0 or current_ask <= current_bid:
            print(f"Invalid market data for {ticker}. Skipping trade.")
            return 0

        try:
            # Calculate mid-price and market spread
            mid_price = (current_bid + current_ask) / 2
            market_spread = current_ask - current_bid

            # Skip trades in excessively wide spread conditions
            MAX_MARKET_SPREAD = 0.035  # Example: Skip if spread > 3.5% of mid-price
            if market_spread / mid_price > MAX_MARKET_SPREAD:
                print(f"Market spread too wide for {ticker}. Skipping trade.")
                return 0

            # Update price history and calculate mean reversion metrics
            self.update_price_history({ticker: security})
            price_history = list(self.price_history[ticker])

            if len(price_history) < 2:  # Require sufficient price history
                print(f"Insufficient price history for {ticker}. Skipping trade.")
                return 0

            # Calculate mean, standard deviation, and Z-score
            mean_price = mean(price_history)
            std_dev_price = stdev(price_history)
            z_score = (mid_price - mean_price) / std_dev_price if std_dev_price > 0 else 0

            # Mean reversion signal: Adjust pricing and size based on Z-score
            mean_reversion_adjustment = 1.0
            if z_score > 2:  # Overbought
                mean_reversion_adjustment = 1.2  # Increase sell aggressiveness
            elif z_score < -2:  # Oversold
                mean_reversion_adjustment = 1.2  # Increase buy aggressiveness

            print(f"{ticker}: Z-Score: {z_score:.2f}, Mean: {mean_price:.2f}, StdDev: {std_dev_price:.2f}")

            # Get configurations
            security_config = self.securities_config[ticker]
            trading_config = TRADING_CONFIG['market_making']
            current_position = self.position_tracker.get_position(ticker)
            max_position = trading_config.max_position_size[ticker]
            base_size = trading_config.base_order_size[ticker]

            # Adjust spread based on volatility and position skew
            spread_multiplier = {
                'LOW': 0.8,    # Tighter spreads for low volatility
                'MEDIUM': 1.0,
                'HIGH': 1.3    # Wider spreads for high volatility
            }[security_config.volatility]

            target_spread = max(security_config.min_spread, self.trading_params.target_spread)
            adjusted_spread = target_spread * spread_multiplier

            # Incorporate position skew
            position_skew = current_position / max_position
            adjusted_spread *= (1 + abs(position_skew) * 0.2)  # Adjust spread for position

            # Cap spread and adjust for mean reversion signals
            MAX_SPREAD = 0.03
            final_spread = min(adjusted_spread, MAX_SPREAD) / mean_reversion_adjustment

            # Calculate sizes based on position and mean reversion signals
            size_multiplier = {
                'LOW': 1.2,
                'MEDIUM': 1.0,
                'HIGH': 0.8
            }[security_config.volatility]

            base_buy_size = base_sell_size = int(base_size * size_multiplier)
            if position_skew > 0:  # Long position
                base_buy_size *= (1 - abs(position_skew))
                base_sell_size *= (1 + abs(position_skew) * mean_reversion_adjustment)
            else:  # Short position
                base_buy_size *= (1 + abs(position_skew) * mean_reversion_adjustment)
                base_sell_size *= (1 - abs(position_skew))

            # Set bid and ask prices with adjusted spread
            half_spread = final_spread / 2
            our_bid = round(mid_price * (1 - half_spread), 2)
            our_ask = round(mid_price * (1 + half_spread), 2)

            # Emergency position reduction
            if abs(position_skew) > 0.8:
                if position_skew > 0:
                    our_ask = current_bid  # Aggressively sell at bid to reduce long position
                    base_sell_size *= 2.5
                    base_buy_size = 0
                else:
                    our_bid = current_ask  # Aggressively buy at ask to reduce short position
                    base_buy_size *= 2.5
                    base_sell_size = 0

            # Apply size limits
            buy_size = min(max(trading_config.min_order_size, int(base_buy_size)), security_config.max_order_size)
            sell_size = min(max(trading_config.min_order_size, int(base_sell_size)), security_config.max_order_size)

            # Cancel stale orders and submit new orders
            self.client.cancel_orders_for_ticker(ticker)
            orders_placed = 0

            if buy_size and abs(current_position) < max_position:
                buy_order = self.client.submit_order(
                    ticker=ticker, type="LIMIT", quantity=buy_size,
                    action="BUY", price=our_bid
                )
                if buy_order:
                    orders_placed += 1
                    print(f"BUY {ticker}: {buy_size} @ ${our_bid:.2f}")

            if sell_size and abs(current_position) < max_position:
                sell_order = self.client.submit_order(
                    ticker=ticker, type="LIMIT", quantity=sell_size,
                    action="SELL", price=our_ask
                )
                if sell_order:
                    orders_placed += 1
                    print(f"SELL {ticker}: {sell_size} @ ${our_ask:.2f}")

            return orders_placed

        except Exception as e:
            print(f"Error executing trades for {ticker}: {str(e)}")
            return 0

    def _log_trade(self, ticker: str, size: int, bid: float, ask: float):
        """Log trade information"""
        if LOG_CONFIG['level'] == 'OFF':
            return
            
        self.trade_count += 1
        current_position = self.position_tracker.get_position(ticker)
        
        print(f"\nTrade #{self.trade_count} - {ticker}")
        print(f"Time: {time.strftime('%H:%M:%S')}")
        print(f"Size: {size}")
        print(f"Bid: ${bid:.2f} | Ask: ${ask:.2f}")
        print(f"Current Position: {current_position}")
        print("-" * 40)

    def print_pnl_summary(self):
        """Print current P&L summary"""
        trader_info = self.client._make_request("trader")
        if not trader_info:
            return
        
        positions = self.position_tracker.get_all_positions()
        realized_pl = float(trader_info.get('realized_pl', 0))
        unrealized_pl = float(trader_info.get('unrealized_pl', 0))
        total_pl = realized_pl + unrealized_pl
        
        if any(positions.values()) or total_pl != 0:
            print(f"\nP&L Summary @ {time.strftime('%H:%M:%S')}")
            print("-" * 40)
            
            for ticker, position in positions.items():
                if position != 0:
                    print(f"{ticker:4s}: Pos: {position:5d}")
            
            print(f"Realized P&L:   ${realized_pl:,.2f}")
            print(f"Unrealized P&L: ${unrealized_pl:,.2f}")
            print(f"Total P&L:      ${total_pl:,.2f}\n")