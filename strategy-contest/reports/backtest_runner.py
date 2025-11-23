import sys
import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import statistics

# Add base-bot-template to path
base_path = os.path.join(os.path.dirname(__file__), '..', 'base-bot-template')
if not os.path.exists(base_path):
    base_path = '/app/base'
sys.path.insert(0, base_path)

# Add strategy path
strategy_path = os.path.join(os.path.dirname(__file__), '..', 'swing-reversion-strategy')
sys.path.insert(0, strategy_path)

from strategy_interface import BaseStrategy, Signal, Portfolio
from exchange_interface import MarketSnapshot, TradeExecution, Exchange
from your_strategy import SwingReversionStrategy

class BacktestExchange:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.current_idx = 0
        self.name = "backtest"
        
    def fetch_market_snapshot(self, symbol: str, *, limit: int) -> MarketSnapshot:
        # Return data up to current_idx
        # We need 'limit' amount of history ending at current_idx
        
        end_idx = self.current_idx + 1
        start_idx = max(0, end_idx - limit)
        
        slice_df = self.data.iloc[start_idx:end_idx]
        prices = slice_df['Close'].tolist()
        current_price = prices[-1]
        timestamp = slice_df.index[-1]
        
        return MarketSnapshot(
            symbol=symbol,
            prices=prices,
            current_price=current_price,
            timestamp=timestamp
        )

    def execute_trade(self, symbol: str, side: str, size: float, price: float) -> TradeExecution:
        # In backtest, we assume execution at the requested price (or close price)
        # For simplicity, use the price passed (which usually comes from current market snapshot)
        timestamp = self.data.index[self.current_idx]
        return TradeExecution(side=side, size=size, price=price, timestamp=timestamp)

def run_backtest():
    # 1. Download Data
    print("Downloading data...")
    # Contest period: Jan-Jun 2024
    start_date = "2024-01-01"
    end_date = "2024-06-30"
    symbol = "BTC-USD"
    
    df = yf.download(symbol, start=start_date, end=end_date, interval="1h")
    
    if isinstance(df.columns, pd.MultiIndex):
        try:
            df.columns = df.columns.droplevel('Ticker')
        except:
            pass

    if df.empty:
        print("No data downloaded!")
        return

    print(f"Downloaded {len(df)} candles.")
    print("Columns:", df.columns)
    print(df.head())

    # 2. Setup
    exchange = BacktestExchange(df)
    config = {
        "ma_period": 24,
        "grid_step_pct": 0.01,
        "max_grid_levels": 2,
        "position_size_pct": 0.275,
        "stop_loss_pct": 0.15,
        "take_profit_above_sma_pct": 0.50,
        "trailing_stop_activation_pct": 0.025,
        "trailing_stop_callback_pct": 0.035
    }
    
    strategy = SwingReversionStrategy(config, exchange)
    
    portfolio = Portfolio(symbol=symbol, cash=10000.0, quantity=0.0)
    
    trades = []
    equity_curve = []
    
    # 3. Loop
    # We need enough history for MA (50 periods)
    start_idx = 50
    
    for i in range(start_idx, len(df)):
        exchange.current_idx = i
        current_price = df['Close'].iloc[i]
        timestamp = df.index[i]
        
        # Get Signal
        # We need to pass enough history. 
        # fetch_market_snapshot handles this if we ask for enough.
        # Strategy asks for history? No, strategy uses market.prices.
        # We should ensure market.prices has at least ma_period.
        
        market = exchange.fetch_market_snapshot(symbol, limit=100)
        signal = strategy.generate_signal(market, portfolio)
        
        if signal.action == "buy":
            cost = signal.size * current_price
            if portfolio.cash >= cost:
                portfolio.cash -= cost
                portfolio.quantity += signal.size
                trades.append({
                    "timestamp": timestamp,
                    "side": "buy",
                    "price": current_price,
                    "size": signal.size,
                    "cost": cost
                })
                strategy.on_trade(signal, current_price, signal.size, timestamp)
                
        elif signal.action == "sell":
            if portfolio.quantity >= signal.size:
                revenue = signal.size * current_price
                portfolio.cash += revenue
                portfolio.quantity -= signal.size
                trades.append({
                    "timestamp": timestamp,
                    "side": "sell",
                    "price": current_price,
                    "size": signal.size,
                    "revenue": revenue
                })
                strategy.on_trade(signal, current_price, signal.size, timestamp)

        # Track Equity
        equity = portfolio.value(current_price)
        equity_curve.append(equity)

    # 4. Report
    final_equity = equity_curve[-1]
    pnl = final_equity - 10000.0
    pnl_pct = (pnl / 10000.0) * 100
    
    print("-" * 40)
    print(f"Backtest Complete")
    print(f"Final Equity: ${final_equity:,.2f}")
    print(f"PnL: ${pnl:,.2f} ({pnl_pct:.2f}%)")
    print(f"Total Trades: {len(trades)}")
    
    # Calculate Drawdown
    peak = 10000.0
    max_drawdown = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak
        if dd > max_drawdown:
            max_drawdown = dd
            
    print(f"Max Drawdown: {max_drawdown*100:.2f}%")
    print("-" * 40)
    
    # Save Report
    with open("reports/backtest_report.md", "w") as f:
        f.write(f"# Backtest Report\n\n")
        f.write(f"- **Symbol**: {symbol}\n")
        f.write(f"- **Period**: {start_date} to {end_date}\n")
        f.write(f"- **Final Equity**: ${final_equity:,.2f}\n")
        f.write(f"- **PnL**: ${pnl:,.2f} ({pnl_pct:.2f}%)\n")
        f.write(f"- **Max Drawdown**: {max_drawdown*100:.2f}%\n")
        f.write(f"- **Total Trades**: {len(trades)}\n")

if __name__ == "__main__":
    run_backtest()
