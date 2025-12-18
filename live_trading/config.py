"""
Alpaca Paper Trading Configuration
Configuration settings for IBIT overnight trading strategy implementation.
"""

import os
from pathlib import Path

# Alpaca API Configuration
# You'll need to set these in your environment or update directly
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY', 'PKAB74KBMZ4M6EQIHXA62WNGO7')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY', 'D5TAZgiJgC7MFTTRX3Bx4rrvXCEe7JfcrdpBTfmb9DCJ')
ALPACA_BASE_URL = 'https://paper-api.alpaca.markets'  # Paper trading endpoint
ALPACA_ACCOUNT_ID = '901343204'  # Account reference (optional)

# Trading Configuration
SYMBOL = 'IBIT'  # iShares Bitcoin Trust ETF
POSITION_SIZE_PCT = 0.95  # Use 95% of available buying power
MIN_POSITION_SIZE = 100  # Minimum dollar amount to trade
MAX_POSITION_SIZE = 10000  # Maximum dollar amount per trade

# Risk Management
# MAX_DAILY_LOSS = 0.05  # Disabled - no daily loss limit
# MAX_TOTAL_DRAWDOWN = 0.20  # Disabled - no total drawdown limit

# Trading Schedule (Eastern Time)
MARKET_CLOSE_HOUR = 15  # 3:50 PM ET - buy 10 minutes before close
MARKET_CLOSE_MINUTE = 50
MARKET_OPEN_HOUR = 9   # 9:40 AM ET - sell 10 minutes after open
MARKET_OPEN_MINUTE = 40

# Logging and Monitoring
LOG_LEVEL = 'INFO'
ENABLE_EMAIL_ALERTS = True
EMAIL_RECIPIENTS = ['derickdavidjones@gmail.com']

# Daily Email Reports
ENABLE_DAILY_EMAIL_REPORTS = True
DAILY_REPORT_TIME_HOUR = 17  # 5:00 PM ET - after market close
DAILY_REPORT_TIME_MINUTE = 30
EMAIL_SMTP_SERVER = 'smtp.gmail.com'  # Gmail SMTP
EMAIL_SMTP_PORT = 587
EMAIL_FROM = 'derickdavidjones@gmail.com'  # Sender email
EMAIL_APP_PASSWORD = 'uuhiugcxrvitnolz'  # Gmail App Password

# Data Storage
DATA_DIR = Path(__file__).parent / 'data'
LOGS_DIR = Path(__file__).parent / 'logs'
RESULTS_DIR = Path(__file__).parent / 'results'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Performance Tracking
PERFORMANCE_UPDATE_FREQUENCY = 'daily'  # How often to update performance metrics
BACKUP_FREQUENCY = 'weekly'  # How often to backup trade data

# Paper Trading Validation
VALIDATE_ORDERS = True  # Double-check orders before submission
DRY_RUN_MODE = False   # Set to True to simulate without actual orders