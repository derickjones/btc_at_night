"""
Configuration file for IBIT overnight trading strategy backtesting.
"""

from datetime import datetime

# Backtesting parameters
START_DATE = "2021-10-19"  # IBIT launch date
END_DATE = datetime.now().strftime("%Y-%m-%d")
INITIAL_CAPITAL = 10000.0

# Trading parameters
SYMBOL = "IBIT"
TRANSACTION_COST = 0.0  # 0.0% - Alpaca has commission-free trading
SLIPPAGE = 0.0001  # 0.01% minimal slippage for liquid ETF like IBIT

# Market hours (US Eastern Time)
MARKET_OPEN_TIME = "09:30"
MARKET_CLOSE_TIME = "16:00"

# Strategy timing (5 minutes offset from market open/close)
BUY_TIME = "15:55"   # Buy 5 minutes before market close
SELL_TIME = "09:35"  # Sell 5 minutes after market open

# Risk management
MAX_POSITION_SIZE = 1.0  # 100% of capital (no leverage)
MIN_POSITION_SIZE = 0.0  # Minimum position size

# Data settings
DATA_SOURCE = "yahoo"
TIMEZONE = "US/Eastern"

# Output settings
SAVE_RESULTS = True
RESULTS_DIR = "results"
PLOT_RESULTS = True
VERBOSE = True