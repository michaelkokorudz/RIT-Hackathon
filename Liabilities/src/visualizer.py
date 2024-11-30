import matplotlib.pyplot as plt
from collections import deque

class MarketVisualizer:
    def __init__(self):
        self.max_points_full = 600  # Full session range
        self.max_points_window = 100  # Sliding window range
        self.default_y_padding_factor = 0.1  # 10% padding for y-axis

        # Fixed y-axis ranges for full plots
        self.abc_full_y_range = (46, 54)
        self.xyz_full_y_range = (21, 27.5)

        self._initialize_visualizer()
        plt.show(block=False)

    def _initialize_visualizer(self):
        plt.ion()  # Enable interactive mode
        self.fig, ((self.ax1, self.ax3), (self.ax2, self.ax4)) = plt.subplots(2, 2, figsize=(16, 12))  # 4 graphs

        # Initialize data structures for historical data (full and window)
        self.abc_data_full = self._init_data_structure(self.max_points_full)
        self.xyz_data_full = self._init_data_structure(self.max_points_full)
        self.abc_data_window = self._init_data_structure(self.max_points_window)
        self.xyz_data_window = self._init_data_structure(self.max_points_window)

        self.last_tick = None  # Track the last tick processed

        # Initialize tender offers per ticker
        self.tenders_per_ticker = {'ABC': [], 'XYZ': []}

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

        # Reset data if current_tick is 0
        if current_tick == 0:
            print("Current tick is 0. Resetting data.")
            self._reset_data()

        self.last_tick = current_tick

        # Check if securities data is valid
        if not securities:
            print("No securities data available. Skipping update.")
            return

        # Get current securities data
        abc_security = next((s for s in securities if s['ticker'] == 'ABC'), None)
        xyz_security = next((s for s in securities if s['ticker'] == 'XYZ'), None)

        if not (abc_security and xyz_security):
            print("Missing securities data for ABC or XYZ. Skipping update.")
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

    def _reset_data(self):
        """Resets the data structures and clears the plots without closing the figure."""
        # Reset data structures
        for data_dict in [self.abc_data_full, self.xyz_data_full, self.abc_data_window, self.xyz_data_window]:
            for key in data_dict:
                data_dict[key].clear()
        self.last_tick = None
        self.tenders_per_ticker = {'ABC': [], 'XYZ': []}
        print("Data structures have been reset.")

        # Clear the plots
        self._clear_graph()
        print("Plots have been cleared.")

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
                    # Keep only the 3 most recent tenders
                    self.tenders_per_ticker[ticker] = self.tenders_per_ticker[ticker][-3:]

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
            tender_price = tender['price']
            tender_action = tender['action']

            # Solid line for the first 25 ticks
            solid_end_tick = start_tick + 25
            solid_end_tick = min(solid_end_tick, 600)  # Ensure it doesn't exceed 600

            # Dotted line from solid_end_tick to the end of x-axis
            if x_range:
                dotted_end_tick = x_range[1]
            else:
                dotted_end_tick = 600  # Default end tick

            # Ensure the lines don't go beyond the x-axis limit
            solid_end_tick = min(solid_end_tick, dotted_end_tick)

            # Skip plotting if the tender is outside the x-axis range
            if x_range and start_tick > x_range[1]:
                continue

            # Adjust the line to fit within the x-axis range
            plot_start_tick = max(start_tick, x_range[0]) if x_range else start_tick
            plot_solid_end_tick = max(min(solid_end_tick, x_range[1]), plot_start_tick)
            plot_dotted_end_tick = max(min(dotted_end_tick, x_range[1]), plot_solid_end_tick)

            # Plot solid line for the first 25 ticks
            if plot_start_tick < plot_solid_end_tick:
                ax.hlines(y=tender_price, xmin=plot_start_tick, xmax=plot_solid_end_tick, color='purple', linestyle='-', linewidth=2)

            # Plot dotted line from solid_end_tick to dotted_end_tick
            if plot_solid_end_tick < plot_dotted_end_tick:
                ax.hlines(y=tender_price, xmin=plot_solid_end_tick, xmax=plot_dotted_end_tick, color='purple', linestyle=':', linewidth=2)

            # Adjust label to include action
            label_text = f"{tender_action} Tender ${tender_price:.2f}"

            # Add label at the start of the tender
            ax.text(plot_start_tick, tender_price, label_text, color='purple', fontsize=9, ha='left', va='bottom')

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
        ax.legend(loc='upper right', fontsize=10)

    def _clear_graph(self):
        """Clears the graph entirely."""
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        self.fig.canvas.draw()
        print("Graph cleared.")

    def reset(self):
        """Resets the visualizer by clearing all data and reinitializing the plots."""
        # Close the figure
        plt.close(self.fig)
        print("Figure closed. Reinitializing visualizer.")

        # Reinitialize the visualizer
        self._initialize_visualizer()
        plt.show(block=False)
        print("Visualizer has been reset.")
