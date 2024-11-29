import matplotlib.pyplot as plt
from collections import deque
import time

class MarketVisualizer:
    def __init__(self):
        plt.ion()
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.max_points = 100
        
        # Initialize deques for historical data
        self.abc_data = {
            'ticks': deque(maxlen=self.max_points),
            'prices': deque(maxlen=self.max_points),
            'bids': deque(maxlen=self.max_points),
            'asks': deque(maxlen=self.max_points)
        }
        self.xyz_data = {
            'ticks': deque(maxlen=self.max_points),
            'prices': deque(maxlen=self.max_points),
            'bids': deque(maxlen=self.max_points),
            'asks': deque(maxlen=self.max_points)
        }
        
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

        # Update data structures
        self._update_security_data(self.abc_data, abc_history, abc_security)
        self._update_security_data(self.xyz_data, xyz_history, xyz_security)
        
        self._draw_plots(abc_security, xyz_security)

    def _update_security_data(self, data_dict, history, current):
        # Initialize data structures if empty
        if not data_dict['ticks']:
            # Load historical data first
            for i, entry in enumerate(history[-self.max_points:]):
                data_dict['ticks'].append(i)  # Use sequential numbers for ticks
                data_dict['prices'].append(entry['close'])
                data_dict['bids'].append(entry['close'])
                data_dict['asks'].append(entry['close'])
        else:
            # Get the next tick number
            next_tick = data_dict['ticks'][-1] + 1
            
            # Add current data point
            data_dict['ticks'].append(next_tick)
            data_dict['prices'].append(current['last'])
            data_dict['bids'].append(current['bid'])
            data_dict['asks'].append(current['ask'])

    def _draw_plots(self, abc_security, xyz_security):
        self.ax1.clear()
        self.ax2.clear()
        
        self._plot_security(self.ax1, 'ABC', self.abc_data, abc_security)
        self._plot_security(self.ax2, 'XYZ', self.xyz_data, xyz_security)

        plt.tight_layout()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _plot_security(self, ax, ticker, data, security):
        if not data['prices']:
            return

        # Convert deques to lists for plotting
        ticks = list(data['ticks'])
        prices = list(data['prices'])
        bids = list(data['bids'])
        asks = list(data['asks'])

        # Plot lines
        ax.plot(ticks, prices, 'b-', label='Price', linewidth=1.5)
        ax.plot(ticks, bids, 'r--', label=f'Bid ${security["bid"]:.2f}', alpha=0.5)
        ax.plot(ticks, asks, 'g--', label=f'Ask ${security["ask"]:.2f}', alpha=0.5)

        # Dynamic y-axis limits based on min/max with padding
        all_values = prices + bids + asks
        y_min, y_max = min(all_values), max(all_values)
        padding = (y_max - y_min) * 0.1 if y_max != y_min else 0.1
        ax.set_ylim(y_min - padding, y_max + padding)

        # Customize plot
        ax.set_title(f'{ticker} Stock Price: ${security["last"]:.2f}')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')