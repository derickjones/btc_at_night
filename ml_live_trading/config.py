"""
ML Live Trading Configuration
Configuration settings for ML-enhanced IBIT overnight trading strategy.
Uses a SEPARATE Alpaca account from the baseline strategy.
"""

import os
from pathlib import Path

# =============================================================================
# ALPACA API CONFIGURATION (DIFFERENT ACCOUNT FROM BASELINE)
# =============================================================================
# Set these environment variables for your SECOND Alpaca paper trading account:
#   ML_ALPACA_API_KEY
#   ML_ALPACA_SECRET_KEY
# Or update the default values below

ALPACA_API_KEY = os.getenv('ML_ALPACA_API_KEY', 'PK5CVE3IJVB5LJP3AB5LRXBCXF')
ALPACA_SECRET_KEY = os.getenv('ML_ALPACA_SECRET_KEY', '7Swg8smiQYCqEascWpTVzeXEuHKrQpHL9bSeLWhaFQYs')
ALPACA_BASE_URL = 'https://paper-api.alpaca.markets'  # Paper trading endpoint (library adds /v2)

# =============================================================================
# TRADING CONFIGURATION
# =============================================================================
SYMBOL = 'IBIT'  # iShares Bitcoin Trust ETF
POSITION_SIZE_PCT = 0.95  # Use 95% of available buying power
MIN_POSITION_SIZE = 100  # Minimum dollar amount to trade
MAX_POSITION_SIZE = 10000  # Maximum dollar amount per trade

# Order validation
VALIDATE_ORDERS = True

# =============================================================================
# ML MODEL CONFIGURATION
# =============================================================================
# Probability threshold for buy signal (model outputs probability 0-1)
# Higher threshold = more selective, fewer trades
# Lower threshold = more aggressive, more trades
ML_BUY_THRESHOLD = 0.5  # Buy when model predicts >50% chance of positive overnight

# Model type to use (matches trained models)
# Options: 'logistic_regression', 'random_forest', 'xgboost', 'gradient_boosting'
ML_MODEL_TYPE = 'logistic_regression'  # Best performer in backtest

# =============================================================================
# TRADING SCHEDULE (Eastern Time)
# =============================================================================
MARKET_CLOSE_HOUR = 15  # 3:50 PM ET - buy 10 minutes before close
MARKET_CLOSE_MINUTE = 50
MARKET_OPEN_HOUR = 9   # 9:31 AM ET - sell just after market open
MARKET_OPEN_MINUTE = 31

# =============================================================================
# LOGGING AND MONITORING
# =============================================================================
LOG_LEVEL = 'INFO'
ENABLE_EMAIL_ALERTS = False  # Disable for now, enable when ready

# =============================================================================
# DATA STORAGE
# =============================================================================
DATA_DIR = Path(__file__).parent / 'data'
LOGS_DIR = Path(__file__).parent / 'logs'
RESULTS_DIR = Path(__file__).parent / 'results'
MODELS_DIR = Path(__file__).parent / 'models'

# Create directories if they don't exist
for dir_path in [DATA_DIR, LOGS_DIR, RESULTS_DIR, MODELS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)
