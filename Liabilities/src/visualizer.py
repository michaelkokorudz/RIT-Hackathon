import matplotlib.pyplot as plt
from collections import deque

class MarketVisualizer:
    def __init__(self):
        plt.ion()  # Enable interactive mode
        self.fig, ((self.ax1, self.ax3), (self.ax2, self.ax4)) = plt.subplots(2, 2, figsize=(16, 12))  # 4 graphs
        self.max_points_full = 600  # Full session range
        self.max_points_window = 100  # Sliding window range
        self.default_y_padding_factor = 0.1  # 10% padding for y-axis

        # Fixed y-axis ranges for full plots
        self.abc_full_y_range = (45, 55)
        self.xyz_full_y_range = (21.5, 27.5)

        # Initialize data structures for historical data (full and window)
        self.abc_data_full = self._init_data_structure(self.max_points_full)
        self.xyz_data_full = self._init_data_structure(self.max_points_full)
        self.abc_data_window = self._init_data_structure(self.max_points_window)
        self.xyz_data_window = self._init_data_structure(self.max_points_window)

        self.last_tick = None  # Track the last tick processed

        # Initialize tender offers per ticker
        self.tenders_per_ticker = {'ABC': [], 'XYZ': []}

        plt.show(block=False)

    def _init_data_structure(self, maxlen):
        return {
            'ticks': deque(maxlen=maxlen),
            'prices': deque(maxlen=maxlen),
            'bids': deque(maxlen=maxlen),
            'asks': deque(maxlen=maxlen),
        }

    def update(self, securities, tenders, current_tick):
        """
        Update the visualizer with the latest data.
        """
        print(f"Current tick: {current_tick}")
        print(f"Securities: {securities}")
        print(f"Tenders: {tenders}")

        if self.last_tick == current_tick:
            print("No new tick, skipping update.")
            return

        self.last_tick = current_tick

        # Get current securities data
        abc_security = next((s for s in securities if s['ticker'] == 'ABC'), {})
        xyz_security = next((s for s in securities if s['ticker'] == 'XYZ'), {})
        
        if not (abc_security and xyz_security):
            print("Missing securities data.")
            return

        # Process tenders
        self._process_tenders(tenders)

        # Update full data structures
        self._update_security_data_full(self.abc_data_full, abc_security, current_tick)
        self._update_security_data_full(self.xyz_data_full, xyz_security, current_tick)

        # Update sliding window data (based on the full data)
        self._update_security_data_window(self.abc_data_window, self.abc_data_full)
        self._update_security_data_window(self.xyz_data_window, self.xyz_data_full)

        # Draw plots
        self._draw_plots(abc_security, xyz_security)

    def _process_tenders(self, tenders):
        """Process the incoming tenders and update tender lists."""
        for tender in tenders:
            ticker = tender['ticker']
            tick = tender['tick']
            price = tender['price']
            action = tender['action']
            if ticker in self.tenders_per_ticker:
                # Check if tender is already recorded
                if not any(t['tick'] == tick for t in self.tenders_per_ticker[ticker]):
                    self.tenders_per_ticker[ticker].append({'tick': tick, 'price': price, 'action': action})

        # Remove expired tenders from the window (if necessary)
        for ticker in self.tenders_per_ticker:
            self.tenders_per_ticker[ticker] = [
                tender for tender in self.tenders_per_ticker[ticker]
                if self.last_tick <= tender['tick'] + 30  # Tender is still active (within 30 ticks from its start)
            ]

    def _update_security_data_full(self, data_dict, current, current_tick):
        """Update the full range data with the latest data point."""
        # Add current data point if it's new
        if not data_dict['ticks'] or data_dict['ticks'][-1] != current_tick:
            data_dict['ticks'].append(current_tick)
            data_dict['prices'].append(current.get('last', 0))
            data_dict['bids'].append(current.get('bid', 0))
            data_dict['asks'].append(current.get('ask', 0))

    def _update_security_data_window(self, window_dict, full_dict):
        """
        Update the sliding window graph with the latest data.
        Adjust the window to include data from left_limit to current_tick.
        """
        buffer = 30
        right_limit = min(self.last_tick + buffer, 600)
        left_limit = max(0, right_limit - self.max_points_window)

        # Extract indices where tick is within [left_limit, self.last_tick]
        ticks_list = list(full_dict['ticks'])
        indices = [i for i, tick in enumerate(ticks_list) if left_limit <= tick <= self.last_tick]

        # Collect data from those indices
        window_dict['ticks'] = deque([full_dict['ticks'][i] for i in indices], maxlen=self.max_points_window)
        window_dict['prices'] = deque([full_dict['prices'][i] for i in indices], maxlen=self.max_points_window)
        window_dict['bids'] = deque([full_dict['bids'][i] for i in indices], maxlen=self.max_points_window)
        window_dict['asks'] = deque([full_dict['asks'][i] for i in indices], maxlen=self.max_points_window)

    def _draw_plots(self, abc_security, xyz_security):
        # Clear all axes
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()

        # Full tick range plots with fixed x-axis from 0 to 600 and fixed y-axis range
        self._plot_security(self.ax1, 'ABC (Full)', self.abc_data_full, abc_security, ticker='ABC', x_range=(0, 600), y_range=self.abc_full_y_range)
        self._plot_security(self.ax2, 'XYZ (Full)', self.xyz_data_full, xyz_security, ticker='XYZ', x_range=(0, 600), y_range=self.xyz_full_y_range)

        # Calculate x-axis range for window plots with 30 ticks buffer
        buffer = 30
        right_limit = min(self.last_tick + buffer, 600)
        left_limit = max(0, right_limit - self.max_points_window)
        x_range_window = (left_limit, right_limit)

        # Sliding window plots with dynamic y-axis limits and slight padding
        self._plot_security(self.ax3, 'ABC (Window)', self.abc_data_window, abc_security, ticker='ABC', x_range=x_range_window, y_padding_factor=0.05)
        self._plot_security(self.ax4, 'XYZ (Window)', self.xyz_data_window, xyz_security, ticker='XYZ', x_range=x_range_window, y_padding_factor=0.05)

        plt.tight_layout()
        self.fig.canvas.draw()
        plt.pause(0.01)  # Refresh the plots dynamically

    def _plot_security(self, ax, title, data, security, ticker='', x_range=None, y_range=None, y_padding_factor=None):
        if not data['prices']:
            print(f"No price data available for {title}.")
            return

        # Convert deques to lists for plotting
        ticks = list(data['ticks'])
        prices = list(data['prices'])
        bids = list(data['bids'])
        asks = list(data['asks'])

        # Plot lines
        ax.plot(ticks, prices, 'b-', label='Price', linewidth=2)
        ax.plot(ticks, bids, 'r--', label=f'Bid ${security.get("bid", 0):.2f}', alpha=0.7)
        ax.plot(ticks, asks, 'g--', label=f'Ask ${security.get("ask", 0):.2f}', alpha=0.7)

        # Plot tender offers
        tender_events = self.tenders_per_ticker.get(ticker, [])
        for tender in tender_events:
            start_tick = tender['tick']
            end_tick = start_tick + 30  # Project 30 ticks into the future
            tender_price = tender['price']
            tender_action = tender['action']
            # Ensure the line doesn't go beyond the x-axis limit
            end_tick = min(end_tick, 600)

            # Skip plotting tender if it is outside the x-axis range
            if x_range and (end_tick < x_range[0] or start_tick > x_range[1]):
                continue

            # Adjust the line to fit within the x-axis range
            plot_start_tick = max(start_tick, x_range[0]) if x_range else start_tick
            plot_end_tick = min(end_tick, x_range[1]) if x_range else end_tick

            # Plot horizontal line representing the tender offer duration
            ax.hlines(y=tender_price, xmin=plot_start_tick, xmax=plot_end_tick, color='purple', linestyle='-', linewidth=2)

            # Adjust label to include action
            label_text = f"{tender_action} Tender ${tender_price:.2f}"

            # Add label at the middle of the line
            mid_tick = (plot_start_tick + plot_end_tick) / 2
            ax.text(mid_tick, tender_price, label_text, color='purple', fontsize=9, ha='center', va='bottom')

        # Set x limits
        if x_range:
            ax.set_xlim(x_range)
        else:
            ax.set_xlim([min(ticks), max(ticks)])

        # Set y limits
        if y_range:
            ax.set_ylim(y_range)
        else:
            # Adjust y limits based on data with slight padding
            y_min = min(min(prices), min(bids), min(asks))
            y_max = max(max(prices), max(bids), max(asks))
            # Include tender prices in y-axis limits
            tender_prices = [t['price'] for t in tender_events]
            if tender_prices:
                y_min = min(y_min, min(tender_prices))
                y_max = max(y_max, max(tender_prices))
            padding_factor = y_padding_factor if y_padding_factor is not None else self.default_y_padding_factor
            padding = (y_max - y_min) * padding_factor
            ax.set_ylim([y_min - padding, y_max + padding])

        # Customize plot
        ax.set_title(f'{title}: ${security.get("last", 0):.2f}', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', fontsize=10)

    def _clear_graph(self):
        """Clears the graph entirely."""
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        self.fig.canvas.draw()
        print("Graph cleared.")

    def reset(self):
        """Resets the visualizer by clearing all data and closing the plots."""
        # Clear the data structures
        self.abc_data_full = self._init_data_structure(self.max_points_full)
        self.xyz_data_full = self._init_data_structure(self.max_points_full)
        self.abc_data_window = self._init_data_structure(self.max_points_window)
        self.xyz_data_window = self._init_data_structure(self.max_points_window)
        self.tenders_per_ticker = {'ABC': [], 'XYZ': []}
        self.last_tick = None

        # Clear the plots
        self._clear_graph()

        # Close the figure
        plt.close(self.fig)
        print("Visualizer has been reset.")
