from typing import Dict, Optional
from src.config import SecurityConfig

class PositionTracker:
    def __init__(self, config: Dict[str, SecurityConfig]):
        """Initialize position tracker with security configurations"""
        print("Initializing PositionTracker")
        
        self.positions = {ticker: 0 for ticker in config.keys()}
        self.config = config
        
        # Track position costs for P&L calculations
        self.position_costs = {ticker: 0.0 for ticker in config.keys()}
        self.last_prices = {ticker: 0.0 for ticker in config.keys()}
        
        # Track order history
        self.pending_orders = {ticker: [] for ticker in config.keys()}
        
        print(f"Initialized positions: {self.positions}")
    
    def update_position(self, ticker: str, change: int, price: Optional[float] = None, verbose: bool = False) -> bool:
        """
        Update position for a given ticker
        Returns True if update was successful, False if it would violate limits
        """
        if ticker not in self.positions:
            print(f"Warning: Cannot update position for unknown ticker {ticker}")
            return False
            
        new_position = self.positions[ticker] + change
        
        # Check position limits
        if abs(new_position) > self.config[ticker].position_limit:
            if verbose:
                print(f"Warning: Position change rejected - would exceed position limit for {ticker}")
            return False
        
        # Update position
        self.positions[ticker] = new_position
        
        # Update cost basis if price provided
        if price is not None:
            if change > 0:  # Buying
                self.position_costs[ticker] += change * price
            else:  # Selling
                avg_cost = self.position_costs[ticker] / self.positions[ticker] if self.positions[ticker] != 0 else price
                self.position_costs[ticker] += change * avg_cost
            
            self.last_prices[ticker] = price
        
        if verbose:
            print(f"Updated position for {ticker}: {self.positions[ticker]}")
        
        return True
    
    def get_position(self, ticker: str) -> int:
        """Get current position for a ticker"""
        return self.positions.get(ticker, 0)
    
    def get_all_positions(self) -> Dict[str, int]:
        """Get all current positions"""
        return self.positions.copy()
    
    def can_trade(self, ticker: str, quantity: int, action: str) -> bool:
        """
        Check if a trade would violate any position limits
        action should be 'BUY' or 'SELL'
        """
        if ticker not in self.positions:
            return False
            
        # Calculate position change
        change = quantity if action == 'BUY' else -quantity
        new_position = self.positions[ticker] + change
        
        # Check position limits
        return abs(new_position) <= self.config[ticker].position_limit
    
    def get_position_value(self, ticker: str) -> float:
        """Get current position value using last known price"""
        return self.positions[ticker] * self.last_prices.get(ticker, 0.0)
    
    def reset_positions(self):
        """Reset all positions to zero"""
        self.positions = {ticker: 0 for ticker in self.positions.keys()}
        self.position_costs = {ticker: 0.0 for ticker in self.positions.keys()}
        print("All positions reset to zero")