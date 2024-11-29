import requests
import json
import matplotlib.pyplot as plt
from datetime import datetime
import time
from collections import deque
import numpy as np

# Load API settings
with open('settings.json') as f:
    settings = json.load(f)

API_KEY = settings['API_KEY']
BASE_URL = settings['URL']

class RITClient:
    def __init__(self, settings):
        self.api_key = settings['API_KEY']
        self.user = settings['USER']
        self.password = settings['PASSWORD']
        self.headers = {
            'X-API-Key': self.api_key,
            'Authorization': f"Basic {self.user}:{self.password}"
        }
        
    def _make_request(self, endpoint, params=None):
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(
                url, 
                headers=self.headers,
                params=params,
                timeout=5,
                auth=(self.user, self.password)
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Request failed: {e}")
            return None

    def get_securities(self):
        return self._make_request("/v1/securities")
    
    def get_ticker_history(self, ticker):
        return self._make_request("/v1/securities/history", params={'ticker': ticker})

class MarketVisualizer:
    def __init__(self):
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.max_points = 100
        
        # Initialize deques for both securities including bid/ask
        self.abc_prices = deque(maxlen=self.max_points)
        self.abc_bids = deque(maxlen=self.max_points)
        self.abc_asks = deque(maxlen=self.max_points)
        self.xyz_prices = deque(maxlen=self.max_points)
        self.xyz_bids = deque(maxlen=self.max_points)
        self.xyz_asks = deque(maxlen=self.max_points)
        self.ticks = deque(maxlen=self.max_points)
        
        plt.ion()

    def update(self, securities, abc_history, xyz_history):
        self.fig.clear()
        self.ax1, self.ax2 = self.fig.subplots(2, 1)
        
        # Clear existing data
        self.abc_prices.clear()
        self.abc_bids.clear()
        self.abc_asks.clear()
        self.xyz_prices.clear()
        self.xyz_bids.clear()
        self.xyz_asks.clear()
        self.ticks.clear()
        
        # Get current bid/ask prices
        current_abc_bid = next((s['bid'] for s in securities if s['ticker'] == 'ABC'), None)
        current_abc_ask = next((s['ask'] for s in securities if s['ticker'] == 'ABC'), None)
        current_xyz_bid = next((s['bid'] for s in securities if s['ticker'] == 'XYZ'), None)
        current_xyz_ask = next((s['ask'] for s in securities if s['ticker'] == 'XYZ'), None)
        
        # Update prices and bid/ask
        for hist_data in abc_history:
            self.abc_prices.append(hist_data['close'])
            self.abc_bids.append(current_abc_bid)
            self.abc_asks.append(current_abc_ask)
            self.ticks.append(hist_data['tick'])
            
        for hist_data in xyz_history:
            self.xyz_prices.append(hist_data['close'])
            self.xyz_bids.append(current_xyz_bid)
            self.xyz_asks.append(current_xyz_ask)

        # Calculate the number of points to leave clear (20% of max_points)
        clear_points = int(self.max_points * 0.2)
        plot_ticks = list(self.ticks) + [max(self.ticks) + i for i in range(1, clear_points + 1)]
        
        # Extend bid/ask lines into the clear area
        extended_abc_bids = list(self.abc_bids) + [current_abc_bid] * clear_points
        extended_abc_asks = list(self.abc_asks) + [current_abc_ask] * clear_points
        extended_xyz_bids = list(self.xyz_bids) + [current_xyz_bid] * clear_points
        extended_xyz_asks = list(self.xyz_asks) + [current_xyz_ask] * clear_points
        
        # Plot historical prices
        self.ax1.plot(list(self.ticks), list(self.abc_prices), label='ABC Price', color='blue')
        self.ax2.plot(list(self.ticks), list(self.xyz_prices), label='XYZ Price', color='blue')
        
        # Plot bid/ask lines with extended clear area
        self.ax1.plot(plot_ticks, extended_abc_bids, '--', color='red', 
                     label=f'Bid (${current_abc_bid:.2f})', alpha=0.5)
        self.ax1.plot(plot_ticks, extended_abc_asks, '--', color='green', 
                     label=f'Ask (${current_abc_ask:.2f})', alpha=0.5)
        self.ax2.plot(plot_ticks, extended_xyz_bids, '--', color='red', 
                     label=f'Bid (${current_xyz_bid:.2f})', alpha=0.5)
        self.ax2.plot(plot_ticks, extended_xyz_asks, '--', color='green', 
                     label=f'Ask (${current_xyz_ask:.2f})', alpha=0.5)
        
        # Customize plots
        self.ax1.set_title('ABC Stock')
        self.ax2.set_title('XYZ Stock')
        self.ax1.grid(True)
        self.ax2.grid(True)
        self.ax1.legend()
        self.ax2.legend()
        
        plt.tight_layout()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.1)

def main():
    client = RITClient(settings)
    visualizer = MarketVisualizer()
    
    try:
        while True:
            securities = client.get_securities()
            abc_history = client.get_ticker_history('ABC')
            xyz_history = client.get_ticker_history('XYZ')
            
            if all([securities, abc_history, xyz_history]):
                visualizer.update(securities, abc_history, xyz_history)
            
            time.sleep(2)  # Update every 2 seconds
            
    except KeyboardInterrupt:
        print("\nStopping market data monitoring...")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
