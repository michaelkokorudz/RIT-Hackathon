from typing import Dict
from src.config import SecurityConfig, TRADING_LIMITS

class PositionTracker:
    def __init__(self, config: Dict[str, SecurityConfig]):
        print(f"Initializing PositionTracker")
        
        self.positions = {ticker: 0 for ticker in config.keys()}
        self.config = config
        
        print(f"Initialized positions: {self.positions}")
        
    def update_position(self, ticker: str, quantity: int) -> None:
        if ticker not in self.positions:
            print(f"Warning: Received unknown ticker {ticker}")
            return
            
        self.positions[ticker] += quantity
        print(f"Updated position for {ticker}: {self.positions[ticker]}")
        
    def can_trade(self, ticker: str, quantity: int) -> bool:
        """Check if a trade would violate any limits"""
        if ticker not in self.positions:
            print(f"Warning: Cannot check trade for unknown ticker {ticker}")
            return False
            
        # Calculate potential new position
        new_position = self.positions[ticker] + quantity
        
        # Check individual security limit
        if abs(new_position) > self.config[ticker].position_limit:
            return False
            
        # Calculate gross exposure
        gross_exposure = sum(abs(pos) for pos in self.positions.values())
        gross_exposure += abs(quantity)
        
        # Calculate net exposure
        net_exposure = sum(pos for pos in self.positions.values())
        net_exposure += quantity
        
        return (gross_exposure <= TRADING_LIMITS.gross_limit and
                abs(net_exposure) <= TRADING_LIMITS.net_limit)