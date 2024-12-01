import json
import os
import matplotlib.pyplot as plt
from typing import Dict
from src.client import RITClient
from src.visualizer import MarketVisualizer
from src.position_tracker import PositionTracker
from src.config import SECURITIES_CONFIG, TRADING_CONFIG
from src.trader import Trader
import time

def load_settings():
    """Load settings from configuration files"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(current_dir, 'settings.json')
    
    try:
        with open(settings_path) as f:
            settings = json.load(f)
        return settings
    except FileNotFoundError:
        raise FileNotFoundError(f"Settings file not found: {settings_path}")

def main():
    # Initialize components
    settings = load_settings()
    client = RITClient(settings)
    position_tracker = PositionTracker(SECURITIES_CONFIG)
    trader = Trader(client, position_tracker, SECURITIES_CONFIG)
    visualizer = MarketVisualizer()
    
    print("\n=== Trading System Initialized ===")
    print(f"Trading securities: {list(SECURITIES_CONFIG.keys())}")
    print(f"Update interval: {TRADING_CONFIG['market_making'].order_refresh_time}s")
    print("=" * 40 + "\n")
    
    # Trading loop variables
    last_pnl_update = time.time()
    orders_this_second = 0
    MAX_ORDERS_PER_SECOND = 10
    current_pnl = 0.0  # Initialize PNL tracking
    
    try:
        while True:
            # Get current securities data
            securities = client.get_securities()
            if not securities:
                time.sleep(0.1)
                continue
            
            # Filter for our tracked securities
            tracked_securities = [s for s in securities if s['ticker'] in SECURITIES_CONFIG]
            
            # Update price history
            trader.update_price_history({s['ticker']: s for s in tracked_securities})
            
            # Execute trading strategy
            current_time = time.time()
            
            # Get current P&L
            trader_info = client._make_request("trader")
            if trader_info:
                realized_pl = float(trader_info.get('realized_pl', 0))
                unrealized_pl = float(trader_info.get('unrealized_pl', 0))
                current_pnl = realized_pl + unrealized_pl
            
            # Print P&L summary every 5 seconds
            if current_time - last_pnl_update >= 5:
                trader.print_pnl_summary()
                last_pnl_update = current_time
            
            # Execute trades for each security
            for security in tracked_securities:
                if orders_this_second < MAX_ORDERS_PER_SECOND:
                    new_orders = trader.execute_trades(security)
                    orders_this_second += new_orders
            
            # Reset orders counter every second
            if current_time - int(current_time) < 0.1:
                orders_this_second = 0
            
            # Update visualization with current P&L
            visualizer.update(tracked_securities, trader.price_history, current_pnl)
            plt.pause(0.001)
            
            # Sleep to prevent overwhelming the API
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopping trading system...")
        client.cancel_all_orders()
        plt.close('all')
        
    except Exception as e:
        print(f"\nError occurred: {e}")
        client.cancel_all_orders()
        plt.close('all')
        raise

if __name__ == "__main__":
    main()