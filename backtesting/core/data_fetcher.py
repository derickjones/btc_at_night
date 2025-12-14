"""
Data fetcher module for IBIT trading data.
Handles data collection, cleaning, and preparation for backtesting.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import pytz
from datetime import datetime, time
from typing import Optional, Tuple
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class IBITDataFetcher:
    """Fetches and processes IBIT data for backtesting."""
    
    def __init__(self, symbol: str = config.SYMBOL):
        self.symbol = symbol
        self.timezone = pytz.timezone(config.TIMEZONE)
        
    def fetch_data(self, start_date: str, end_date: str, interval: str = "1d") -> pd.DataFrame:
        """
        Fetch IBIT data from Yahoo Finance.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval ("1d" for daily, "1m" for minute)
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = yf.Ticker(self.symbol)
            
            # For minute data, Yahoo Finance has limitations (only ~7 days)
            # So we'll use daily data for backtesting and approximate the intraday timing
            data = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if data.empty:
                raise ValueError(f"No data found for {self.symbol} between {start_date} and {end_date}")
                
            # For daily data, ensure timezone is set correctly
            if interval == "1d":
                if data.index.tz is None:
                    data.index = data.index.tz_localize('US/Eastern')
                else:
                    data.index = data.index.tz_convert('US/Eastern')
            else:
                # For minute data
                if data.index.tz is None:
                    data.index = data.index.tz_localize('US/Eastern')
                else:
                    data.index = data.index.tz_convert('US/Eastern')
                
            return data
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            raise
    
    def get_trading_days(self, start_date: str, end_date: str) -> pd.DatetimeIndex:
        """
        Get trading days between start and end date.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            DatetimeIndex of trading days
        """
        # Fetch daily data to get trading days
        ticker = yf.Ticker(self.symbol)
        daily_data = ticker.history(start=start_date, end=end_date, interval="1d")
        
        return daily_data.index.date
    
    def get_entry_exit_prices(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Extract entry (buy) and exit (sell) prices based on strategy timing.
        Uses daily OHLC data: buy at close price, sell at next day's open price.
        
        Args:
            data: Daily OHLCV data
            
        Returns:
            DataFrame with entry and exit prices for each trading day
        """
        results = []
        
        # Convert to list for easier indexing
        dates = data.index.tolist()
        
        for i in range(len(dates) - 1):  # -1 because we need next day data
            current_date = dates[i]
            next_date = dates[i + 1]
            
            try:
                # Buy at close price (simulating 5 minutes before close)
                buy_price = data.loc[current_date, 'Close']
                
                # Sell at next day's open price (simulating 5 minutes after open)
                sell_price = data.loc[next_date, 'Open']
                
                # Calculate return
                trade_return = (sell_price - buy_price) / buy_price
                
                # Calculate holding period (overnight)
                holding_period_hours = 17.5  # Approximate overnight hours (4 PM to 9:30 AM)
                
                results.append({
                    'trade_date': current_date.date(),
                    'buy_date': current_date,
                    'sell_date': next_date,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'return': trade_return,
                    'holding_period_hours': holding_period_hours
                })
                    
            except Exception as e:
                print(f"Error processing date {current_date}: {e}")
                continue
        
        return pd.DataFrame(results)
    
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate the data.
        
        Args:
            data: Raw OHLCV data
            
        Returns:
            Cleaned DataFrame
        """
        # Remove any rows with missing values
        data = data.dropna()
        
        # Remove any rows with zero or negative prices
        price_columns = ['Open', 'High', 'Low', 'Close']
        for col in price_columns:
            if col in data.columns:
                data = data[data[col] > 0]
        
        # Remove any obvious outliers (prices that change more than 50% in one minute)
        if 'Close' in data.columns and len(data) > 1:
            price_change = data['Close'].pct_change().abs()
            data = data[price_change < 0.5]  # Remove changes > 50%
        
        # Ensure volume is non-negative
        if 'Volume' in data.columns:
            data = data[data['Volume'] >= 0]
        
        return data
    
    def save_data(self, data: pd.DataFrame, filename: str) -> None:
        """
        Save data to CSV file.
        
        Args:
            data: DataFrame to save
            filename: Name of the file (without extension)
        """
        filepath = f"data/{filename}.csv"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        data.to_csv(filepath)
        print(f"Data saved to {filepath}")
    
    def load_data(self, filename: str) -> Optional[pd.DataFrame]:
        """
        Load data from CSV file.
        
        Args:
            filename: Name of the file (without extension)
            
        Returns:
            DataFrame if file exists, None otherwise
        """
        filepath = f"data/{filename}.csv"
        if os.path.exists(filepath):
            data = pd.read_csv(filepath, index_col=0, parse_dates=True)
            return data
        return None
    
    def get_strategy_data(self, start_date: str = config.START_DATE, 
                         end_date: str = config.END_DATE, 
                         use_cache: bool = True) -> pd.DataFrame:
        """
        Get complete strategy data with entry/exit prices.
        
        Args:
            start_date: Start date for backtesting
            end_date: End date for backtesting
            use_cache: Whether to use cached data if available
            
        Returns:
            DataFrame with strategy data
        """
        cache_filename = f"{self.symbol}_strategy_data_{start_date}_{end_date}"
        
        # Try to load from cache first
        if use_cache:
            cached_data = self.load_data(cache_filename)
            if cached_data is not None:
                print(f"Loaded cached data from {cache_filename}.csv")
                return cached_data
        
        print(f"Fetching fresh data for {self.symbol} from {start_date} to {end_date}...")
        
        # Fetch daily data (more reliable and covers longer periods)
        raw_data = self.fetch_data(start_date, end_date, interval="1d")
        clean_data = self.clean_data(raw_data)
        
        # Extract strategy-specific prices
        strategy_data = self.get_entry_exit_prices(clean_data)
        
        if use_cache:
            self.save_data(strategy_data, cache_filename)
        
        return strategy_data


if __name__ == "__main__":
    # Test the data fetcher
    fetcher = IBITDataFetcher()
    
    # Test with a small date range
    test_start = "2024-01-01"
    test_end = "2024-01-31"
    
    print(f"Testing data fetch for {test_start} to {test_end}")
    strategy_data = fetcher.get_strategy_data(test_start, test_end)
    
    print(f"\nStrategy data shape: {strategy_data.shape}")
    if not strategy_data.empty:
        print("\nFirst few rows:")
        print(strategy_data.head())
        print(f"\nAverage return per trade: {strategy_data['return'].mean():.4f}")
        print(f"Total trades: {len(strategy_data)}")