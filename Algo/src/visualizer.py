import matplotlib.pyplot as plt
from collections import deque
import time
from typing import Dict, List, Any, Optional
from src.config import VISUALIZATION_CONFIG, SecurityConfig

class MarketVisualizer:
    def __init__(self):
        plt.ion()
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4), (self.ax_pnl, self.ax_combined)) = plt.subplots(
            3, 2, 
            figsize=VISUALIZATION_CONFIG['figure_size']
        )
        self.max_points = VISUALIZATION_CONFIG['max_price_points']
        
        # Initialize data structures with type hints
        self.securities_data: Dict[str, Dict[str, deque]] = {
            ticker: self._create_security_deques()
            for ticker in ['OWL', 'CROW', 'DOVE', 'DUCK']
        }
        
        self.security_axes: Dict[str, plt.Axes] = {
            'OWL': self.ax1,
            'CROW': self.ax2,
            'DOVE': self.ax3,
            'DUCK': self.ax4
        }
        
        # Initialize P&L tracking
        self.pnl_data: Dict[str, deque] = {
            'times': deque(maxlen=VISUALIZATION_CONFIG['max_pnl_points']),
            'total_pnl': deque(maxlen=VISUALIZATION_CONFIG['max_pnl_points'])
        }
        
        # Initialize combined price tracking
        self.combined_data: Dict[str, Dict[str, deque]] = {
            ticker: {
                'times': deque(maxlen=600),
                'prices': deque(maxlen=600)
            } for ticker in ['OWL', 'CROW', 'DOVE', 'DUCK']
        }
        
        self.start_time: Optional[float] = None
        plt.show(block=False)

    def _create_security_deques(self) -> Dict[str, deque]:
        """Create deques for a security's data with proper typing"""
        return {
            'ticks': deque(maxlen=self.max_points),
            'prices': deque(maxlen=self.max_points),
            'bids': deque(maxlen=self.max_points),
            'asks': deque(maxlen=self.max_points)
        }

    def update(self, 
              securities: List[Dict[str, Any]], 
              histories: Dict[str, List[Dict[str, Any]]], 
              current_pnl: float
    ) -> None:
        """Update visualization with new market data"""
        if self.start_time is None:
            self.start_time = time.time()
        
        current_time = time.time() - self.start_time
        
        # Update existing security plots
        for ticker in self.securities_data.keys():
            security = next((s for s in securities if s['ticker'] == ticker), None)
            history = histories.get(ticker)
            
            if security and history:
                self._update_security_data(self.securities_data[ticker], history, security)
                
                # Update combined price data
                self.combined_data[ticker]['times'].append(current_time)
                self.combined_data[ticker]['prices'].append(security['last'])
        
        # Update P&L data
        self.pnl_data['times'].append(current_time)
        self.pnl_data['total_pnl'].append(current_pnl)
        
        self._draw_plots(securities)
        self._draw_pnl()
        self._draw_combined_prices()

    def _update_security_data(self, 
                            data_dict: Dict[str, deque], 
                            history: List[Dict[str, Any]], 
                            current: Dict[str, Any]
    ) -> None:
        """Update price history for a single security"""
        if not data_dict['ticks']:
            # Load historical data first
            for i, entry in enumerate(history[-self.max_points:]):
                data_dict['ticks'].append(i)
                data_dict['prices'].append(entry['close'])
                data_dict['bids'].append(entry['close'])
                data_dict['asks'].append(entry['close'])
        else:
            next_tick = data_dict['ticks'][-1] + 1
            data_dict['ticks'].append(next_tick)
            data_dict['prices'].append(current['last'])
            data_dict['bids'].append(current['bid'])
            data_dict['asks'].append(current['ask'])

    def _draw_plots(self, securities: List[Dict[str, Any]]) -> None:
        """Draw individual security plots"""
        # Clear all axes
        for ax in self.security_axes.values():
            ax.clear()
        
        # Update each security plot
        for ticker, security in self.securities_data.items():
            current_security = next((s for s in securities if s['ticker'] == ticker), None)
            if current_security:
                self._plot_security(
                    self.security_axes[ticker],
                    ticker,
                    security,
                    current_security
                )

        plt.tight_layout()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _plot_security(self, 
                      ax: plt.Axes, 
                      ticker: str, 
                      data: Dict[str, deque], 
                      security: Dict[str, Any]
    ) -> None:
        """Plot a single security's data"""
        if not data['prices']:
            return

        # Convert deques to lists for plotting
        ticks = list(data['ticks'])
        prices = list(data['prices'])
        bids = list(data['bids'])
        asks = list(data['asks'])

        # Plot lines with improved styling
        ax.plot(ticks, prices, 'b-', label='Price', linewidth=1.5)
        ax.plot(ticks, bids, 'r--', label=f'Bid ${security["bid"]:.2f}', alpha=0.5)
        ax.plot(ticks, asks, 'g--', label=f'Ask ${security["ask"]:.2f}', alpha=0.5)

        # Dynamic y-axis limits with padding
        all_values = prices + bids + asks
        y_min, y_max = min(all_values), max(all_values)
        padding = (y_max - y_min) * 0.1 if y_max != y_min else 0.1
        ax.set_ylim(y_min - padding, y_max + padding)

        # Customize plot appearance
        ax.set_title(f'{ticker} Price: ${security["last"]:.2f}')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', fontsize='small')

    def _draw_pnl(self) -> None:
        """Draw P&L chart"""
        self.ax_pnl.clear()
        self.ax_pnl.plot(
            list(self.pnl_data['times']), 
            list(self.pnl_data['total_pnl']), 
            'g-', 
            label='Total P&L'
        )
        self.ax_pnl.set_title('Trading P&L')
        self.ax_pnl.grid(True, alpha=0.3)
        self.ax_pnl.legend()
        self.ax_pnl.set_xlabel('Time (seconds)')
        self.ax_pnl.set_ylabel('P&L ($)')

    def _draw_combined_prices(self) -> None:
        """Draw combined price chart"""
        self.ax_combined.clear()
        for ticker in self.combined_data:
            self.ax_combined.plot(
                list(self.combined_data[ticker]['times']),
                list(self.combined_data[ticker]['prices']),
                label=ticker,
                linewidth=1.0
            )
        self.ax_combined.set_title('Combined Price History')
        self.ax_combined.grid(True, alpha=0.3)
        self.ax_combined.legend()
        self.ax_combined.set_xlabel('Time (seconds)')
        self.ax_combined.set_ylabel('Price ($)')