import json
import os
import matplotlib.pyplot as plt
from typing import Dict, Any
from src.client import RITClient, OrderType, OrderAction
from src.visualizer import MarketVisualizer
from src.position_tracker import PositionTracker
from src.config import SECURITIES_CONFIG, SecurityConfig
from src.trader import MeanReversionTrader
import traceback
import time

def load_settings():
    # Get the directory containing this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(current_dir, 'settings.json')
        
    try:
        with open(settings_path) as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"settings.json not found at {settings_path}")

def calculate_optimal_spread(security: Dict[str, Any], config: SecurityConfig) -> float:
    """Calculate optimal spread based on volatility and fee structure"""
    base_spread = 0.02  # Minimum spread
    
    # Adjust spread based on volatility
    volatility_multiplier = {
        'LOW': 1.0,
        'MEDIUM': 1.5,
        'HIGH': 2.0
    }[config.volatility]
    
    # Consider fee structure
    fee_cost = abs(config.market_fee) + abs(config.limit_rebate)
    
    # Final spread calculation
    optimal_spread = (base_spread * volatility_multiplier) + fee_cost
    return optimal_spread

def calculate_order_size(
    ticker: str,
    security: Dict[str, Any],
    config: SecurityConfig,
    position_tracker: PositionTracker
) -> int:
    """Calculate optimal order size based on multiple factors"""
    current_position = position_tracker.positions[ticker]
    max_size = config.max_order_size
    position_limit = config.position_limit
    
    # Base size calculation
    remaining_capacity = position_limit - abs(current_position)
    
    # Adjust base size based on fee structure
    if config.limit_rebate > 0:
        # For positive rebate securities (OWL, DUCK), be more aggressive
        base_size = min(2000, remaining_capacity)
    else:
        # For negative rebate securities (CROW, DOVE), be more conservative
        base_size = min(1000, remaining_capacity)
    
    # Adjust size based on volatility
    volatility_scalar = {
        'LOW': 1.0,
        'MEDIUM': 0.7,  # More conservative
        'HIGH': 0.4     # Much more conservative
    }[config.volatility]
    
    # Adjust size based on spread
    current_spread = security['ask'] - security['bid']
    target_spread = calculate_optimal_spread(security, config)
    spread_scalar = min(1.0, (target_spread / current_spread) ** 2) if current_spread > 0 else 0.3
    
    # Position-based adjustment
    position_scalar = 1.0 - (abs(current_position) / position_limit) ** 0.5
    
    # Calculate final size
    optimal_size = int(base_size * volatility_scalar * spread_scalar * position_scalar)
    
    # Ensure minimum size and round to nearest lot size
    lot_size = 100
    optimal_size = max(lot_size, round(optimal_size / lot_size) * lot_size)
    
    return min(optimal_size, max_size)

def main():
    settings = load_settings()
    client = RITClient(settings)
    visualizer = MarketVisualizer()
    position_tracker = PositionTracker(SECURITIES_CONFIG)
    trader = MeanReversionTrader(client, position_tracker, SECURITIES_CONFIG)
    
    try:
        last_order_time = time.time()
        orders_this_second = 0
        MAX_ORDERS_PER_SECOND = 45
        start_time = time.time()
        
        while True:
            # Get current securities data
            all_securities = client.get_securities()
            if not all_securities:
                time.sleep(0.1)
                continue
            
            tracked_securities = [s for s in all_securities if s['ticker'] in SECURITIES_CONFIG]
            
            # Cancel existing orders before placing new ones
            client.cancel_all_orders()
            
            # Only fetch historical data in the first 30 seconds
            elapsed_time = time.time() - start_time
            if elapsed_time <= 30:
                all_histories = {ticker: client.get_ticker_history(ticker) 
                               for ticker in SECURITIES_CONFIG.keys()}
            else:
                # After 30 seconds, just use current data
                all_histories = {
                    ticker: [{
                        'close': security['last'],
                        'time': time.time()
                    }] for security in tracked_securities
                    for ticker in [security['ticker']]
                }
            
            # Rest of your trading logic...
            for security in tracked_securities:
                ticker = security['ticker']
                current_bid = security['bid']
                current_ask = security['ask']
                
                # Trading logic here...
                
            # Update visualization less frequently after initial period
            if len(tracked_securities) == len(SECURITIES_CONFIG):
                current_pnl = trader.calculate_pnl({s['ticker']: s for s in tracked_securities})
                visualizer.update(tracked_securities, all_histories, current_pnl)
                plt.pause(0.001)
            
            # Rate limiting
            current_time = time.time()
            if current_time - last_order_time >= 1:
                orders_this_second = 0
                last_order_time = current_time
            
            if orders_this_second >= MAX_ORDERS_PER_SECOND:
                time.sleep(0.1)
            
            # Adaptive sleep based on elapsed time
            sleep_time = 0.1 if elapsed_time <= 30 else 0.2
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        print("\nStopping trading...")
        client.cancel_all_orders()
        plt.close('all')
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        plt.close('all')

if __name__ == "__main__":
    main()