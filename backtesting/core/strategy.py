"""
Trading strategy implementation for IBIT overnight trading.
Handles position sizing, transaction costs, and trade execution logic.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class IBITOvernightStrategy:
    """
    Implements the IBIT overnight trading strategy:
    - Buy at market close
    - Sell at next day's market open
    - Hold overnight
    """
    
    def __init__(self, initial_capital: float = config.INITIAL_CAPITAL,
                 transaction_cost: float = config.TRANSACTION_COST,
                 slippage: float = config.SLIPPAGE):
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
        self.slippage = slippage
        self.current_capital = initial_capital
        self.position = 0  # Number of shares held
        self.trades = []
        
    def calculate_position_size(self, price: float, capital: float) -> int:
        """
        Calculate number of shares to buy with available capital.
        
        Args:
            price: Price per share
            capital: Available capital
            
        Returns:
            Number of shares to buy
        """
        # Account for transaction costs
        effective_capital = capital * (1 - self.transaction_cost - self.slippage)
        shares = int(effective_capital / price)
        return max(0, shares)
    
    def execute_buy(self, price: float, date: pd.Timestamp) -> Dict:
        """
        Execute buy order at market close.
        
        Args:
            price: Close price
            date: Trade date
            
        Returns:
            Trade information
        """
        if self.position > 0:
            # Already have position, skip
            return None
            
        shares = self.calculate_position_size(price, self.current_capital)
        if shares == 0:
            return None
            
        # Calculate costs
        trade_value = shares * price
        total_cost = trade_value * (1 + self.transaction_cost + self.slippage)
        
        if total_cost > self.current_capital:
            return None
            
        # Execute trade
        self.position = shares
        self.current_capital -= total_cost
        
        trade_info = {
            'type': 'buy',
            'date': date,
            'price': price,
            'shares': shares,
            'value': trade_value,
            'cost': total_cost,
            'capital_after': self.current_capital
        }
        
        return trade_info
    
    def execute_sell(self, price: float, date: pd.Timestamp) -> Dict:
        """
        Execute sell order at market open.
        
        Args:
            price: Open price
            date: Trade date
            
        Returns:
            Trade information
        """
        if self.position <= 0:
            # No position to sell
            return None
            
        shares = self.position
        trade_value = shares * price
        net_proceeds = trade_value * (1 - self.transaction_cost - self.slippage)
        
        # Execute trade
        self.current_capital += net_proceeds
        self.position = 0
        
        trade_info = {
            'type': 'sell',
            'date': date,
            'price': price,
            'shares': shares,
            'value': trade_value,
            'proceeds': net_proceeds,
            'capital_after': self.current_capital
        }
        
        return trade_info
    
    def run_strategy(self, strategy_data: pd.DataFrame) -> pd.DataFrame:
        """
        Run the complete trading strategy.
        
        Args:
            strategy_data: DataFrame with buy/sell prices and dates
            
        Returns:
            DataFrame with detailed trade results
        """
        detailed_trades = []
        portfolio_values = []
        
        for _, row in strategy_data.iterrows():
            trade_date = row['trade_date']
            buy_date = row['buy_date']
            sell_date = row['sell_date']
            buy_price = row['buy_price']
            sell_price = row['sell_price']
            
            # Execute buy order
            buy_trade = self.execute_buy(buy_price, buy_date)
            
            if buy_trade is None:
                continue  # Skip if couldn't execute buy
                
            # Execute sell order next day
            sell_trade = self.execute_sell(sell_price, sell_date)
            
            if sell_trade is None:
                continue  # Skip if couldn't execute sell
                
            # Calculate trade performance
            trade_return = (sell_trade['proceeds'] - buy_trade['cost']) / buy_trade['cost']
            trade_pnl = sell_trade['proceeds'] - buy_trade['cost']
            
            detailed_trade = {
                'trade_date': trade_date,
                'buy_date': buy_date,
                'sell_date': sell_date,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'shares': buy_trade['shares'],
                'buy_cost': buy_trade['cost'],
                'sell_proceeds': sell_trade['proceeds'],
                'gross_return': row['return'],
                'net_return': trade_return,
                'pnl': trade_pnl,
                'capital_before': buy_trade['cost'] + self.current_capital,
                'capital_after': self.current_capital,
                'portfolio_value': self.current_capital
            }
            
            detailed_trades.append(detailed_trade)
            portfolio_values.append({
                'date': sell_date,
                'portfolio_value': self.current_capital,
                'trade_number': len(detailed_trades)
            })
            
        return pd.DataFrame(detailed_trades)
    
    def reset(self):
        """Reset strategy to initial state."""
        self.current_capital = self.initial_capital
        self.position = 0
        self.trades = []