import matplotlib.pyplot as plt
from collections import deque
import time

class MarketVisualizer:
    def __init__(self):
        plt.ion()
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.max_points = 1000
        
        # Initialize deques
        self.abc_prices = deque(maxlen=self.max_points)
        self.abc_bids = deque(maxlen=self.max_points)
        self.abc_asks = deque(maxlen=self.max_points)
        self.xyz_prices = deque(maxlen=self.max_points)
        self.xyz_bids = deque(maxlen=self.max_points)
        self.xyz_asks = deque(maxlen=self.max_points)
        self.ticks = deque(maxlen=self.max_points)
        
        self.last_update = time.time()
        self.min_update_interval = 0.5
        
        plt.show(block=False)

    def update(self, securities, abc_history, xyz_history):
        # Rate limiting check
        current_time = time.time()
        if current_time - self.last_update < self.min_update_interval:
            return
        self.last_update = current_time

        # Get current securities data
        abc_security = next((s for s in securities if s['ticker'] == 'ABC'), None)
        xyz_security = next((s for s in securities if s['ticker'] == 'XYZ'), None)
        
        if not (abc_security and xyz_security and abc_history and xyz_history):
            return

        # Clear existing data
        self.abc_prices.clear()
        self.abc_bids.clear()
        self.abc_asks.clear()
        self.xyz_prices.clear()
        self.xyz_bids.clear()
        self.xyz_asks.clear()
        self.ticks.clear()

        # Add historical data
        for abc_data, xyz_data in zip(abc_history, xyz_history):
            self.ticks.append(abc_data['tick'])
            self.abc_prices.append(abc_data['close'])
            self.abc_bids.append(abc_data['close'])
            self.abc_asks.append(abc_data['close'])
            self.xyz_prices.append(xyz_data['close'])
            self.xyz_bids.append(xyz_data['close'])
            self.xyz_asks.append(xyz_data['close'])

        # Add current data point if it's newer
        if abc_history and self.ticks[-1] < abc_security['tick']:
            self.ticks.append(abc_security['tick'])
            self.abc_prices.append(abc_security['last'])
            self.abc_bids.append(abc_security['bid'])
            self.abc_asks.append(abc_security['ask'])
            self.xyz_prices.append(xyz_security['last'])
            self.xyz_bids.append(xyz_security['bid'])
            self.xyz_asks.append(xyz_security['ask'])

        self._draw_plots(abc_security, xyz_security)

    def _draw_plots(self, abc_security, xyz_security):
        self.fig.clear()
        self.ax1, self.ax2 = self.fig.subplots(2, 1)
        
        clear_points = int(self.max_points * 0.2)
        plot_ticks = list(self.ticks) + [max(self.ticks) + i for i in range(1, clear_points + 1)]
        
        # Plot ABC
        self._plot_security(self.ax1, 'ABC', self.abc_prices, abc_security, plot_ticks, clear_points)
        # Plot XYZ
        self._plot_security(self.ax2, 'XYZ', self.xyz_prices, xyz_security, plot_ticks, clear_points)

        plt.tight_layout()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _plot_security(self, ax, ticker, prices, security, plot_ticks, clear_points):
        # Plot price line
        ax.plot(list(self.ticks), list(prices), 'b-', label='Price', linewidth=2)
        
        # Plot bid/ask projections
        ax.plot(plot_ticks[-clear_points:], [security['bid']] * clear_points, 'r--', 
               label=f'Bid ${security["bid"]:.2f}', alpha=0.5)
        ax.plot(plot_ticks[-clear_points:], [security['ask']] * clear_points, 'g--', 
               label=f'Ask ${security["ask"]:.2f}', alpha=0.5)

        # Customize plot
        ax.set_title(f'{ticker} Stock')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
        ax.set_xlim(min(self.ticks), max(plot_ticks))
        
        # Set $5 window
        current_price = security['last']
        window_size = 5.0
        y_min = current_price - window_size/2
        y_max = current_price + window_size/2
        ax.set_ylim(y_min, y_max)