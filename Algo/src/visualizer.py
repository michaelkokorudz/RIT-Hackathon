import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from typing import Dict, Any, List
from collections import deque
import numpy as np
import time

class MarketVisualizer:
    def __init__(self):
        """Initialize the market visualizer with plots for each security"""
        self.fig = plt.figure(figsize=(15, 10))
        self.gs = GridSpec(3, 2, figure=self.fig)
        
        # Store data for each security
        self.securities_data = {}
        
        # Configure plot settings
        plt.style.use('dark_background')
        self.fig.patch.set_facecolor('#1C1C1C')
        
        # Initialize P&L plot
        self.pnl_ax = self.fig.add_subplot(self.gs[2, :])
        self.pnl_data = deque(maxlen=100)
        self.pnl_times = deque(maxlen=100)
        
        # Settings
        self.max_points = 100
        plt.ion()  # Enable interactive mode
        
    def _initialize_security(self, ticker: str):
        """Initialize plots for a new security"""
        if ticker not in self.securities_data:
            # Determine subplot position
            position = len(self.securities_data)
            row = position // 2
            col = position % 2
            
            # Create subplot
            ax = self.fig.add_subplot(self.gs[row, col])
            
            self.securities_data[ticker] = {
                'ax': ax,
                'prices': deque(maxlen=self.max_points),
                'times': deque(maxlen=self.max_points),
                'bids': deque(maxlen=self.max_points),
                'asks': deque(maxlen=self.max_points)
            }
            
            # Configure subplot
            ax.set_title(f'{ticker} Price Movement')
            ax.set_xlabel('Time')
            ax.set_ylabel('Price')
            ax.grid(True, alpha=0.3)
    
    def update(self, securities: List[Dict[str, Any]], price_history: Dict[str, deque], current_pnl: float):
        """Update the visualization with new market data"""
        current_time = time.strftime('%H:%M:%S')
        
        # Update security plots
        for security in securities:
            ticker = security['ticker']
            
            # Initialize if new security
            if ticker not in self.securities_data:
                self._initialize_security(ticker)
            
            # Convert deque to list for plotting
            history = list(price_history[ticker])
            self._update_security_data(self.securities_data[ticker], history, security)
        
        # Update P&L plot
        self.pnl_data.append(current_pnl)
        self.pnl_times.append(current_time)
        self._update_pnl_plot()
        
        # Refresh the figure
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    def _update_security_data(self, data: Dict, history: List, security: Dict):
        """Update data for a single security"""
        current_time = time.strftime('%H:%M:%S')
        
        # Add new price data
        if history:
            data['prices'].append(history[-1])  # Latest price
        data['times'].append(current_time)
        data['bids'].append(security['bid'])
        data['asks'].append(security['ask'])
        
        # Update plot
        ax = data['ax']
        ax.clear()
        
        # Plot price, bid, and ask lines
        ax.plot(list(data['times']), list(data['prices']), 'w-', label='Price', alpha=0.8)
        ax.plot(list(data['times']), list(data['bids']), 'g-', label='Bid', alpha=0.5)
        ax.plot(list(data['times']), list(data['asks']), 'r-', label='Ask', alpha=0.5)
        
        # Configure plot
        ax.set_title(f'{security["ticker"]} Price Movement')
        ax.set_xlabel('Time')
        ax.set_ylabel('Price')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Rotate x-axis labels for better readability
        ax.tick_params(axis='x', rotation=45)
    
    def _update_pnl_plot(self):
        """Update the P&L plot"""
        self.pnl_ax.clear()
        
        # Plot P&L line
        self.pnl_ax.plot(list(self.pnl_times), list(self.pnl_data), 'y-', label='P&L')
        
        # Configure plot
        self.pnl_ax.set_title('Profit & Loss')
        self.pnl_ax.set_xlabel('Time')
        self.pnl_ax.set_ylabel('P&L ($)')
        self.pnl_ax.grid(True, alpha=0.3)
        self.pnl_ax.legend()
        
        # Rotate x-axis labels for better readability
        self.pnl_ax.tick_params(axis='x', rotation=45)