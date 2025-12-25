"""
Alpaca Trading Client
Handles connection and basic operations with Alpaca API for paper trading.
"""

import alpaca_trade_api as tradeapi
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import logging
import time
from typing import Optional, Dict, Any, List

from config import (
    ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL,
    SYMBOL, LOGS_DIR, VALIDATE_ORDERS
)


class AlpacaTradingClient:
    """Client for executing IBIT overnight strategy via Alpaca paper trading."""
    
    def __init__(self):
        """Initialize the Alpaca trading client."""
        self.api = None
        self.account = None
        self.logger = self._setup_logging()
        self.connect()
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for trading operations."""
        logger = logging.getLogger('AlpacaTrading')
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = LOGS_DIR / f'alpaca_trading_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def connect(self) -> bool:
        """Connect to Alpaca API and validate credentials."""
        try:
            self.api = tradeapi.REST(
                ALPACA_API_KEY,
                ALPACA_SECRET_KEY,
                ALPACA_BASE_URL,
                api_version='v2'
            )
            
            # Test connection by getting account info
            self.account = self.api.get_account()
            
            self.logger.info("✅ Successfully connected to Alpaca paper trading")
            self.logger.info(f"Account Status: {self.account.status}")
            self.logger.info(f"Buying Power: ${float(self.account.buying_power):,.2f}")
            self.logger.info(f"Portfolio Value: ${float(self.account.portfolio_value):,.2f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Alpaca: {str(e)}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get current account information."""
        try:
            account = self.api.get_account()
            return {
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'cash': float(account.cash),
                'equity': float(account.equity),
                'day_trade_count': getattr(account, 'daytrade_count', 0),
                'pattern_day_trader': getattr(account, 'pattern_day_trader', False)
            }
        except Exception as e:
            self.logger.error(f"Error getting account info: {str(e)}")
            return {}
    
    def get_current_position(self) -> Optional[Dict[str, Any]]:
        """Get current IBIT position."""
        try:
            positions = self.api.list_positions()
            for position in positions:
                if position.symbol == SYMBOL:
                    return {
                        'symbol': position.symbol,
                        'qty': float(position.qty),
                        'market_value': float(position.market_value),
                        'avg_entry_price': float(position.avg_entry_price),
                        'unrealized_pl': float(position.unrealized_pl),
                        'unrealized_plpc': float(position.unrealized_plpc)
                    }
            return None
        except Exception as e:
            self.logger.error(f"Error getting position: {str(e)}")
            return None
    
    def get_latest_price(self) -> Optional[float]:
        """Get the latest price for IBIT."""
        try:
            # Get latest quote
            latest_trade = self.api.get_latest_trade(SYMBOL)
            return float(latest_trade.price)
        except Exception as e:
            self.logger.error(f"Error getting latest price: {str(e)}")
            return None
    
    def place_market_order(self, side: str, qty: int) -> Optional[str]:
        """
        Place a market order.
        
        Args:
            side: 'buy' or 'sell'
            qty: Number of shares
            
        Returns:
            Order ID if successful, None if failed
        """
        try:
            if VALIDATE_ORDERS:
                # Validate order parameters
                if side not in ['buy', 'sell']:
                    self.logger.error(f"Invalid order side: {side}")
                    return None
                
                if qty <= 0:
                    self.logger.error(f"Invalid quantity: {qty}")
                    return None
                
                # Check account status
                account_info = self.get_account_info()
                if side == 'buy' and account_info.get('buying_power', 0) < 100:
                    self.logger.error("Insufficient buying power")
                    return None
            
            # Place the order
            order = self.api.submit_order(
                symbol=SYMBOL,
                qty=qty,
                side=side,
                type='market',
                time_in_force='DAY'
            )
            
            self.logger.info(f"📋 Order placed: {side.upper()} {qty} shares of {SYMBOL}")
            self.logger.info(f"Order ID: {order.id}")
            
            return order.id
            
        except Exception as e:
            self.logger.error(f"❌ Error placing {side} order: {str(e)}")
            return None
    
    def wait_for_order_fill(self, order_id: str, timeout: int = 300) -> bool:
        """
        Wait for order to be filled.
        
        Args:
            order_id: Order ID to monitor
            timeout: Maximum seconds to wait
            
        Returns:
            True if filled, False if timeout or error
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                order = self.api.get_order(order_id)
                
                if order.status == 'filled':
                    self.logger.info(f"✅ Order {order_id} filled at ${float(order.filled_avg_price):.2f}")
                    return True
                elif order.status in ['canceled', 'rejected', 'expired']:
                    self.logger.error(f"❌ Order {order_id} failed: {order.status}")
                    return False
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error checking order status: {str(e)}")
                return False
        
        self.logger.error(f"❌ Order {order_id} not filled within {timeout} seconds")
        return False
    
    def get_order_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent order history."""
        try:
            orders = self.api.list_orders(
                status='all',
                limit=limit,
                nested=False
            )
            
            order_list = []
            for order in orders:
                if order.symbol == SYMBOL:
                    order_list.append({
                        'id': order.id,
                        'symbol': order.symbol,
                        'side': order.side,
                        'qty': float(order.qty),
                        'status': order.status,
                        'submitted_at': order.submitted_at,
                        'filled_at': order.filled_at,
                        'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None,
                        'filled_qty': float(order.filled_qty) if order.filled_qty else 0
                    })
            
            return order_list
            
        except Exception as e:
            self.logger.error(f"Error getting order history: {str(e)}")
            return []
    
    def cancel_all_orders(self) -> bool:
        """Cancel all open orders."""
        try:
            orders = self.api.list_orders(status='open')
            for order in orders:
                if order.symbol == SYMBOL:
                    self.api.cancel_order(order.id)
                    self.logger.info(f"🚫 Canceled order {order.id}")
            return True
        except Exception as e:
            self.logger.error(f"Error canceling orders: {str(e)}")
            return False
    
    def is_market_open(self) -> bool:
        """Check if the market is currently open."""
        try:
            clock = self.api.get_clock()
            return clock.is_open
        except Exception as e:
            self.logger.error(f"Error checking market status: {str(e)}")
            return False
    
    def get_next_market_open(self) -> Optional[datetime]:
        """Get the next market open time."""
        try:
            clock = self.api.get_clock()
            return clock.next_open
        except Exception as e:
            self.logger.error(f"Error getting next market open: {str(e)}")
            return None
    
    def get_next_market_close(self) -> Optional[datetime]:
        """Get the next market close time."""
        try:
            clock = self.api.get_clock()
            return clock.next_close
        except Exception as e:
            self.logger.error(f"Error getting next market close: {str(e)}")
            return None