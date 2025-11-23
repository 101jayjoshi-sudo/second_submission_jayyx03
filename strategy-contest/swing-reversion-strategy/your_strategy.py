
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import deque
import statistics

# Add base-bot-template to path
base_path = os.path.join(os.path.dirname(__file__), '..', 'base-bot-template')
if not os.path.exists(base_path):
    base_path = '/app/base'
sys.path.insert(0, base_path)

from strategy_interface import BaseStrategy, Signal, register_strategy, Portfolio
from exchange_interface import MarketSnapshot

class SwingReversionStrategy(BaseStrategy):
    """
    Swing Reversion Grid Strategy
    
    Logic:
    - Calculates a Moving Average (SMA) as the "anchor" price.
    - Buys when price deviates below the SMA (Mean Reversion).
    - Sells when price returns to the SMA or goes above it.
    - Uses a grid structure to scale in/out.
    """

    def __init__(self, config: Dict[str, Any], exchange):
        super().__init__(config=config, exchange=exchange)
        
        # Strategy Parameters
        self.ma_period = int(config.get("ma_period", 24))
        self.grid_step_pct = float(config.get("grid_step_pct", 0.01)) # 1% step
        self.max_grid_levels = int(config.get("max_grid_levels", 2))
        self.position_size_pct = float(config.get("position_size_pct", 0.275)) # 27.5% per trade
        self.stop_loss_pct = float(config.get("stop_loss_pct", 0.15)) # 15% max drawdown per position
        self.take_profit_above_sma_pct = float(config.get("take_profit_above_sma_pct", 0.50)) # Sell when price > SMA * (1 + this)
        self.trailing_stop_activation_pct = float(config.get("trailing_stop_activation_pct", 0.025)) # 2.5% profit to activate
        self.trailing_stop_callback_pct = float(config.get("trailing_stop_callback_pct", 0.035)) # 3.5% drop to sell
        
        # State
        self.active_positions = [] # List of {'price': float, 'size': float, 'level': int}
        self.last_signal_time = None
        self.trailing_high = 0.0

    # Redefining logic to be more robust with state
    
    def generate_signal(self, market: MarketSnapshot, portfolio: Portfolio) -> Signal:
        if len(market.prices) < self.ma_period:
            return Signal("hold")

        current_price = market.current_price
        sma = statistics.mean(market.prices[-self.ma_period:])
        deviation = (current_price - sma) / sma
        
        # Update Trailing High
        if portfolio.quantity > 0:
            if current_price > self.trailing_high:
                self.trailing_high = current_price
        else:
            self.trailing_high = 0.0

        # 1. Check Sells (Take Profit / Trailing Stop)
        if portfolio.quantity > 0:
            # Calculate Avg Entry
            total_size = sum(p['size'] for p in self.active_positions)
            if total_size > 0:
                avg_entry = sum(p['price'] * p['size'] for p in self.active_positions) / total_size
                
                # Trailing Stop Logic
                # Activate if price > entry * (1 + activation)
                if self.trailing_high > avg_entry * (1 + self.trailing_stop_activation_pct):
                    # Sell if price < high * (1 - callback)
                    if current_price < self.trailing_high * (1 - self.trailing_stop_callback_pct):
                        return Signal("sell", size=portfolio.quantity, reason="Trailing Stop Hit")

        # Sell if Price > SMA * (1 + buffer) (Mean Reversion + Profit)
        # Only if trailing stop hasn't kicked in (or maybe this is a backup target)
        # Let's make this target very high so trailing stop takes precedence usually
        if deviation > self.take_profit_above_sma_pct and portfolio.quantity > 0:
             # Sell everything
             return Signal("sell", size=portfolio.quantity, reason="Mean Reversion: Target Hit")

        # 2. Check Buys (Grid Entry)
        # Only buy if deviation is negative (Price < SMA)
        if deviation < 0:
            # Calculate which level we are in
            # Level 1: -2% to -4%
            # Level 2: -4% to -6%
            # etc.
            level_idx = int(abs(deviation) / self.grid_step_pct)
            
            if level_idx < 1:
                return Signal("hold") # Between 0% and -2%, do nothing (dead zone)
            
            if level_idx > self.max_grid_levels:
                level_idx = self.max_grid_levels
                
            # Check if we have bought this level recently?
            # Or check if we have enough exposure.
            # Simple Grid: Buy if we don't have a position "near" this price.
            
            # Let's look at our active positions (tracked in on_trade)
            # If we have a position within X% of current price, don't buy.
            
            for pos in self.active_positions:
                price_diff_pct = abs(pos['price'] - current_price) / pos['price']
                if price_diff_pct < (self.grid_step_pct * 0.5):
                    return Signal("hold", reason="Position already exists at this level")
            
            # Check Max Exposure (Contest Rule: Max 55%)
            total_equity = portfolio.cash + (portfolio.quantity * current_price)
            current_exposure = (portfolio.quantity * current_price) / total_equity
            
            if current_exposure >= 0.55:
                return Signal("hold", reason="Max exposure reached")
                
            # Buy
            # Size: 10% of Equity?
            buy_amount_usd = total_equity * self.position_size_pct
            if portfolio.cash < buy_amount_usd:
                buy_amount_usd = portfolio.cash
                
            if buy_amount_usd < 10: # Min trade size
                 return Signal("hold", reason="Insufficient cash")
                 
            size = buy_amount_usd / current_price
            return Signal("buy", size=size, reason=f"Grid Buy Level {level_idx}")

        return Signal("hold")

    def on_trade(self, signal: Signal, execution_price: float, execution_size: float, timestamp: datetime) -> None:
        if signal.action == "buy":
            self.active_positions.append({'price': execution_price, 'size': execution_size})
        elif signal.action == "sell":
            # Clear positions on full sell
            self.active_positions = []

    def get_state(self) -> Dict[str, Any]:
        """Save state to database/disk for crash recovery."""
        return {
            "active_positions": self.active_positions,
            "trailing_high": self.trailing_high
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        """Restore state after restart."""
        self.active_positions = state.get("active_positions", [])
        self.trailing_high = state.get("trailing_high", 0.0)

# Register
register_strategy("swing_reversion", lambda cfg, ex: SwingReversionStrategy(cfg, ex))
