from statistics import mean, stdev
from collections import deque
from src.config import TRADING_CONFIG, LOG_CONFIG
import time
from typing import Dict, Any
from src.client import RITClient
from src.position_tracker import PositionTracker
from src.config import SecurityConfig

class MeanReversionTrader:
    def __init__(
        self,
        client: RITClient,
        position_tracker: PositionTracker,
        securities_config: Dict[str, SecurityConfig]
    ):
        self.client = client
        self.position_tracker = position_tracker
        self.securities_config = securities_config
        self.trading_params = TRADING_CONFIG['mean_reversion']
        
        # Initialize price history for each security
        self.price_history = {
            ticker: deque(maxlen=self.trading_params.lookback_period)
            for ticker in securities_config.keys()
        }
        
        # Initialize running statistics
        self.means = {ticker: 0.0 for ticker in securities_config.keys()}
        self.stds = {ticker: 0.0 for ticker in securities_config.keys()}
        
        # Track P&L
        self.positions = {ticker: 0 for ticker in securities_config.keys()}
        self.position_costs = {ticker: 0 for ticker in securities_config.keys()}
        self.total_pnl = 0
        
        # Add trade logging
        self.trade_count = 0
        
        if LOG_CONFIG['level'] != 'OFF':
            print("\n=== Mean Reversion Trader Initialized ===")
            if LOG_CONFIG['level'] == 'ADVANCED':
                print(f"Trading parameters:")
                print(f"- Z-score threshold: {self.trading_params.z_score_threshold}")
                print(f"- Base position size: {self.trading_params.base_position_size}")
                print(f"- Lookback period: {self.trading_params.lookback_period}\n")

    def update_price_history(self, securities):
        """Update price history for each security"""
        for security in securities:
            ticker = security['ticker']
            if ticker in self.price_history:
                self.price_history[ticker].append(security['last'])

    def calculate_signals(self, securities):
        """Calculate trading signals based on mean reversion"""
        signals = {}
        
        for security in securities:
            ticker = security['ticker']
            prices = self.price_history[ticker]
            
            if len(prices) < self.trading_params.min_data_points:
                if LOG_CONFIG['level'] == 'ADVANCED':
                    print(f"Waiting for more data points for {ticker}. Current: {len(prices)}/{self.trading_params.min_data_points}")
                continue
                
            current_price = security['last']
            moving_avg = mean(prices)
            std_dev = stdev(prices)
            
            if std_dev == 0:
                if LOG_CONFIG['level'] == 'ADVANCED':
                    print(f"Zero standard deviation for {ticker}, skipping")
                continue
                
            z_score = (current_price - moving_avg) / std_dev
            
            # Debug print for every security
            if LOG_CONFIG['level'] == 'ADVANCED':
                print(f"\nSignal Analysis - {ticker}:")
                print(f"Price: ${current_price:.2f}")
                print(f"Moving Avg: ${moving_avg:.2f}")
                print(f"Std Dev: ${std_dev:.2f}")
                print(f"Z-score: {z_score:.2f}")
                print(f"Current Position: {self.positions[ticker]}")
            
            # Log market analysis when z-score is close to threshold
            if abs(z_score) > (self.trading_params.z_score_threshold * LOG_CONFIG['thresholds']['z_score_alert']):
                self._log_market_analysis(ticker, current_price, moving_avg, z_score)
            
            # Generate trading signals
            if z_score > self.trading_params.z_score_threshold:
                signals[ticker] = {
                    'action': 'SELL',
                    'price': security['bid'],
                    'size': self._calculate_position_size(ticker, z_score)
                }
                if LOG_CONFIG['level'] != 'OFF':
                    print(f"Generated SELL signal for {ticker} at bid ${security['bid']}")
            elif z_score < -self.trading_params.z_score_threshold:
                signals[ticker] = {
                    'action': 'BUY',
                    'price': security['ask'],
                    'size': self._calculate_position_size(ticker, z_score)
                }
                if LOG_CONFIG['level'] != 'OFF':
                    print(f"Generated BUY signal for {ticker} at ask ${security['ask']}")
                
        if not signals and LOG_CONFIG['level'] == 'ADVANCED':
            print("No trading signals generated this iteration")
                
        return signals

    def _calculate_position_size(self, ticker, z_score):
        """Calculate position size based on z-score and current positions"""
        base_size = self.trading_params.base_position_size
        current_position = self.positions[ticker]
        
        # Reduce position size if we already have a large position
        position_scalar = 1 - (abs(current_position) / self.securities_config[ticker].position_limit)
        
        # Scale by z-score intensity
        z_score_scalar = min(abs(z_score) / self.trading_params.z_score_threshold, self.trading_params.max_z_score_scalar)
        
        size = int(base_size * position_scalar * z_score_scalar)
        
        if LOG_CONFIG['level'] == 'ADVANCED':
            print(f"Position size calculation for {ticker}:")
            print(f"Base size: {base_size}")
            print(f"Position scalar: {position_scalar:.2f}")
            print(f"Z-score scalar: {z_score_scalar:.2f}")
            print(f"Final size: {size}")
        
        return size

    def execute_trades(self, signals):
        """Execute trades based on signals"""
        for ticker, signal in signals.items():
            if self.position_tracker.can_trade(ticker, signal['size']):
                order = self.client.submit_order(
                    ticker=ticker,
                    type='LIMIT',
                    quantity=signal['size'],
                    action=signal['action'],
                    price=signal['price']
                )
                
                if order:
                    self._update_position_tracking(ticker, signal)
                self._log_trade(ticker, signal, bool(order))

    def _update_position_tracking(self, ticker, signal):
        """Update position and P&L tracking"""
        quantity = signal['size'] if signal['action'] == 'BUY' else -signal['size']
        self.positions[ticker] += quantity
        
        # Update position cost basis
        trade_cost = quantity * signal['price']
        self.position_costs[ticker] += trade_cost

    def _log_trade(self, ticker, signal, order_success):
        """Centralized trade logging based on config"""
        if LOG_CONFIG['level'] == 'OFF':
            return
            
        self.trade_count += 1
        
        if LOG_CONFIG['level'] == 'SIMPLE':
            print(f"Trade #{self.trade_count}: {signal['action']} {ticker} x{signal['size']} @ ${signal['price']:.2f}")
            return
            
        if LOG_CONFIG['level'] == 'ADVANCED':
            print(f"\n=== Trade #{self.trade_count} ===")
            print(f"Time: {time.strftime('%H:%M:%S')}")
            print(f"Security: {ticker}")
            print(f"Action: {signal['action']}")
            print(f"Size: {signal['size']}")
            print(f"Price: ${signal['price']:.2f}")
            print(f"Current Position: {self.positions[ticker]}")
            
            if order_success:
                print(f"Order executed successfully")
                print(f"New position: {self.positions[ticker]}")
                print(f"Current P&L: ${self.total_pnl:.2f}")
            else:
                print("Order failed to execute")
            print("=" * 30)

    def _log_market_analysis(self, ticker, current_price, moving_avg, z_score):
        """Log market analysis based on config"""
        if LOG_CONFIG['level'] == 'OFF':
            return
            
        if LOG_CONFIG['level'] == 'SIMPLE':
            print(f"{ticker} - Price: ${current_price:.2f}, Z-score: {z_score:.2f}")
            return
            
        if LOG_CONFIG['level'] == 'ADVANCED':
            print(f"\nMarket Analysis - {ticker}:")
            print(f"Current Price: ${current_price:.2f}")
            print(f"Moving Average: ${moving_avg:.2f}")
            print(f"Z-score: {z_score:.2f}")

    def _log_pnl_update(self, positions_info, total_pnl):
        """Log P&L updates based on config"""
        if LOG_CONFIG['level'] == 'OFF':
            return
            
        if LOG_CONFIG['level'] == 'SIMPLE':
            print(f"P&L Update: ${total_pnl:.2f}")
            return
            
        if LOG_CONFIG['level'] == 'ADVANCED':
            print(f"\nP&L Update:")
            for ticker, info in positions_info.items():
                if info['position'] != 0:
                    print(f"{ticker}: Position={info['position']}, " +
                          f"Value=${info['value']:.2f}")
            print(f"Total P&L: ${total_pnl:.2f}\n")

    def calculate_pnl(self, securities: Dict[str, Any]) -> float:
        """Calculate current P&L across all positions"""
        total_pnl = 0.0
        for ticker, position in self.position_tracker.positions.items():
            if position != 0 and ticker in securities:
                current_price = securities[ticker]['last']
                total_pnl += position * current_price
        return total_pnl