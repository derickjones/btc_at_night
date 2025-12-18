"""
IBIT Overnight Trading Strategy - Live Implementation
Executes the IBIT overnight strategy using Alpaca paper trading.
"""

import schedule
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
from pathlib import Path
import logging

from alpaca_client import AlpacaTradingClient
from config import (
    POSITION_SIZE_PCT, MIN_POSITION_SIZE, MAX_POSITION_SIZE,
    MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE,
    MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE, RESULTS_DIR, SYMBOL
)


class IBITOvernightStrategy:
    """Live implementation of the IBIT overnight trading strategy."""
    
    def __init__(self):
        """Initialize the strategy."""
        self.client = AlpacaTradingClient()
        self.logger = self._setup_logging()
        self.trades_file = RESULTS_DIR / 'live_trades.json'
        self.performance_file = RESULTS_DIR / 'live_performance.json'
        
        # Strategy state
        self.is_active = True
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        
        # Load existing trade history
        self.trade_history = self._load_trade_history()
        
        self.logger.info("🚀 IBIT Overnight Strategy initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up strategy-specific logging."""
        logger = logging.getLogger('IBITStrategy')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # File handler
            log_file = RESULTS_DIR / f'strategy_{datetime.now().strftime("%Y%m%d")}.log'
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def _load_trade_history(self) -> list:
        """Load existing trade history from file."""
        if self.trades_file.exists():
            with open(self.trades_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_trade(self, trade_data: dict):
        """Save trade to history file."""
        self.trade_history.append(trade_data)
        with open(self.trades_file, 'w') as f:
            json.dump(self.trade_history, f, indent=2, default=str)
    
    def _update_performance_metrics(self):
        """Update and save performance metrics."""
        if not self.trade_history:
            return
        
        # Calculate metrics from trade history
        trades_df = pd.DataFrame(self.trade_history)
        
        # Calculate returns
        if 'pnl' in trades_df.columns:
            total_pnl = trades_df['pnl'].sum()
            winning_trades = (trades_df['pnl'] > 0).sum()
            losing_trades = (trades_df['pnl'] < 0).sum()
            win_rate = winning_trades / len(trades_df) if len(trades_df) > 0 else 0
            
            avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
            avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
            
            performance = {
                'last_updated': datetime.now(),
                'total_trades': len(trades_df),
                'winning_trades': int(winning_trades),
                'losing_trades': int(losing_trades),
                'win_rate': float(win_rate),
                'total_pnl': float(total_pnl),
                'avg_win': float(avg_win),
                'avg_loss': float(avg_loss),
                'profit_factor': float(abs(avg_win / avg_loss)) if avg_loss != 0 else 0,
                'strategy_status': 'active' if self.is_active else 'stopped'
            }
            
            with open(self.performance_file, 'w') as f:
                json.dump(performance, f, indent=2, default=str)
            
            self.logger.info(f"📊 Performance updated: {len(trades_df)} trades, "
                           f"Win Rate: {win_rate:.1%}, Total PnL: ${total_pnl:.2f}")
    
    def calculate_position_size(self) -> int:
        """Calculate position size based on available buying power."""
        try:
            account_info = self.client.get_account_info()
            buying_power = account_info.get('buying_power', 0)
            
            # Calculate position size based on percentage of buying power
            target_value = buying_power * POSITION_SIZE_PCT
            
            # Apply min/max limits
            target_value = max(MIN_POSITION_SIZE, min(target_value, MAX_POSITION_SIZE))
            
            # Get current IBIT price to calculate shares
            current_price = self.client.get_latest_price()
            if not current_price:
                self.logger.error("Could not get current price")
                return 0
            
            shares = int(target_value / current_price)
            
            self.logger.info(f"💰 Position size: {shares} shares "
                           f"(${target_value:.2f} / ${current_price:.2f} per share)")
            
            return shares
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {str(e)}")
            return 0
    
    def check_risk_limits(self) -> bool:
        """Check if we should stop trading due to risk limits."""
        try:
            # Check daily loss limit
            account_info = self.client.get_account_info()
            portfolio_value = account_info.get('portfolio_value', 0)
            
            # Risk management disabled - running pure strategy
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking risk limits: {str(e)}")
            return False
    
    def execute_buy_signal(self):
        """Execute buy order at market close."""
        if not self.is_active:
            self.logger.info("❌ Strategy inactive - skipping buy signal")
            return
        
        if not self.check_risk_limits():
            self.logger.warning("⚠️ Risk limits exceeded - skipping buy signal")
            return
        
        try:
            # Check if market is open
            if not self.client.is_market_open():
                self.logger.warning("Market is closed - cannot execute buy order")
                return
            
            # Check if we already have a position
            current_position = self.client.get_current_position()
            if current_position and current_position['qty'] > 0:
                self.logger.info(f"Already holding position: {current_position['qty']} shares")
                return
            
            # Calculate position size
            shares = self.calculate_position_size()
            if shares <= 0:
                self.logger.warning("Invalid position size - skipping trade")
                return
            
            # Get current price for logging
            current_price = self.client.get_latest_price()
            
            # Place buy order
            self.logger.info(f"🛒 Executing BUY signal at market close")
            self.logger.info(f"Target: {shares} shares at ~${current_price:.2f}")
            
            order_id = self.client.place_market_order('buy', shares)
            if not order_id:
                self.logger.error("Failed to place buy order")
                return
            
            # Wait for order to fill
            if self.client.wait_for_order_fill(order_id, timeout=60):
                # Record the trade
                trade_data = {
                    'trade_id': len(self.trade_history) + 1,
                    'action': 'buy',
                    'timestamp': datetime.now(),
                    'order_id': order_id,
                    'shares': shares,
                    'expected_price': current_price,
                    'status': 'filled'
                }
                self._save_trade(trade_data)
                self.logger.info(f"✅ Buy order completed successfully")
            else:
                self.logger.error("Buy order did not fill in time")
        
        except Exception as e:
            self.logger.error(f"❌ Error executing buy signal: {str(e)}")
    
    def execute_sell_signal(self):
        """Execute sell order at market open."""
        if not self.is_active:
            self.logger.info("❌ Strategy inactive - skipping sell signal")
            return
        
        try:
            # Check if market is open
            if not self.client.is_market_open():
                self.logger.warning("Market is closed - cannot execute sell order")
                return
            
            # Check current position
            current_position = self.client.get_current_position()
            if not current_position or current_position['qty'] <= 0:
                self.logger.info("No position to sell")
                return
            
            shares_to_sell = int(current_position['qty'])
            current_price = self.client.get_latest_price()
            
            # Place sell order
            self.logger.info(f"🔄 Executing SELL signal at market open")
            self.logger.info(f"Selling: {shares_to_sell} shares at ~${current_price:.2f}")
            
            order_id = self.client.place_market_order('sell', shares_to_sell)
            if not order_id:
                self.logger.error("Failed to place sell order")
                return
            
            # Wait for order to fill
            if self.client.wait_for_order_fill(order_id, timeout=60):
                # Calculate P&L (simplified - would need buy price from last trade)
                unrealized_pl = current_position.get('unrealized_pl', 0)
                
                # Record the trade
                trade_data = {
                    'trade_id': len(self.trade_history) + 1,
                    'action': 'sell',
                    'timestamp': datetime.now(),
                    'order_id': order_id,
                    'shares': shares_to_sell,
                    'expected_price': current_price,
                    'pnl': unrealized_pl,
                    'status': 'filled'
                }
                self._save_trade(trade_data)
                
                # Update metrics
                self.total_trades += 1
                if unrealized_pl > 0:
                    self.winning_trades += 1
                
                self._update_performance_metrics()
                
                self.logger.info(f"✅ Sell order completed: P&L ${unrealized_pl:.2f}")
            else:
                self.logger.error("Sell order did not fill in time")
        
        except Exception as e:
            self.logger.error(f"❌ Error executing sell signal: {str(e)}")
    
    def start_scheduler(self):
        """Start the trading scheduler."""
        self.logger.info("📅 Starting trading scheduler...")
        
        # Schedule buy orders (market close)
        schedule.every().monday.at(f"{MARKET_CLOSE_HOUR:02d}:{MARKET_CLOSE_MINUTE:02d}").do(self.execute_buy_signal)
        schedule.every().tuesday.at(f"{MARKET_CLOSE_HOUR:02d}:{MARKET_CLOSE_MINUTE:02d}").do(self.execute_buy_signal)
        schedule.every().wednesday.at(f"{MARKET_CLOSE_HOUR:02d}:{MARKET_CLOSE_MINUTE:02d}").do(self.execute_buy_signal)
        schedule.every().thursday.at(f"{MARKET_CLOSE_HOUR:02d}:{MARKET_CLOSE_MINUTE:02d}").do(self.execute_buy_signal)
        schedule.every().friday.at(f"{MARKET_CLOSE_HOUR:02d}:{MARKET_CLOSE_MINUTE:02d}").do(self.execute_buy_signal)
        
        # Schedule sell orders (market open)
        schedule.every().tuesday.at(f"{MARKET_OPEN_HOUR:02d}:{MARKET_OPEN_MINUTE:02d}").do(self.execute_sell_signal)
        schedule.every().wednesday.at(f"{MARKET_OPEN_HOUR:02d}:{MARKET_OPEN_MINUTE:02d}").do(self.execute_sell_signal)
        schedule.every().thursday.at(f"{MARKET_OPEN_HOUR:02d}:{MARKET_OPEN_MINUTE:02d}").do(self.execute_sell_signal)
        schedule.every().friday.at(f"{MARKET_OPEN_HOUR:02d}:{MARKET_OPEN_MINUTE:02d}").do(self.execute_sell_signal)
        schedule.every().monday.at(f"{MARKET_OPEN_HOUR:02d}:{MARKET_OPEN_MINUTE:02d}").do(self.execute_sell_signal)
        
        # Schedule daily performance update
        schedule.every().day.at("17:00").do(self._update_performance_metrics)
        
        self.logger.info("✅ Scheduler configured:")
        self.logger.info(f"   - Buy signals: Weekdays at {MARKET_CLOSE_HOUR:02d}:{MARKET_CLOSE_MINUTE:02d}")
        self.logger.info(f"   - Sell signals: Weekdays at {MARKET_OPEN_HOUR:02d}:{MARKET_OPEN_MINUTE:02d}")
        
        # Main scheduler loop
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop_strategy(self):
        """Stop the strategy and cancel open orders."""
        self.logger.info("🛑 Stopping strategy...")
        self.is_active = False
        self.client.cancel_all_orders()
        self._update_performance_metrics()
        self.logger.info("✅ Strategy stopped")


def main():
    """Main entry point for live trading."""
    strategy = IBITOvernightStrategy()
    
    try:
        print("🚀 Starting IBIT Overnight Strategy - Paper Trading")
        print(f"Symbol: {SYMBOL}")
        print(f"Position Size: {POSITION_SIZE_PCT:.0%} of buying power")
        print("Press Ctrl+C to stop")
        
        strategy.start_scheduler()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping strategy...")
        strategy.stop_strategy()
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        strategy.stop_strategy()


if __name__ == "__main__":
    main()