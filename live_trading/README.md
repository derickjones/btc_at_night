# IBIT Overnight Strategy - Live Trading

This folder contains the implementation for live paper trading of the IBIT overnight strategy using Alpaca Markets.

## 🎯 Strategy Overview

The live implementation executes the same IBIT overnight strategy that achieved 183.8% returns in backtesting:
- **Buy IBIT at market close** (4:00 PM ET)
- **Sell IBIT at market open** (9:30 AM ET next day)
- Automated execution via Alpaca paper trading API

## 🛠️ Setup Instructions

### 1. Get Alpaca Paper Trading Account
1. Sign up at [Alpaca Markets](https://alpaca.markets/)
2. Enable paper trading
3. Get your API credentials from the [dashboard](https://app.alpaca.markets/paper/dashboard/overview)

### 2. Install Dependencies
```bash
cd live_trading
pip install -r requirements.txt
```

### 3. Configure API Credentials
Update `config.py` with your Alpaca credentials:
```python
ALPACA_API_KEY = 'your_paper_trading_api_key_here'
ALPACA_SECRET_KEY = 'your_paper_trading_secret_key_here'
```

### 4. Validate Setup
```bash
python setup.py
```
This will verify dependencies, configuration, and API connection.

## 🚀 Running the Strategy

### Start Live Trading
```bash
python strategy.py
```
This starts the automated trading scheduler that will:
- Execute buy orders at market close
- Execute sell orders at market open
- Log all activities
- Monitor risk limits

### Monitor Performance
```bash
python monitor.py
```
Generates:
- Daily performance reports
- Performance charts
- Real-time status updates

## 📁 File Structure

```
live_trading/
├── config.py              # Configuration settings
├── alpaca_client.py        # Alpaca API client
├── strategy.py            # Main trading strategy
├── monitor.py             # Performance monitoring
├── setup.py               # Setup validation
├── requirements.txt       # Dependencies
├── data/                  # Data storage
├── logs/                  # Trading logs
└── results/               # Performance results
    ├── live_trades.json   # Trade history
    ├── live_performance.json # Performance metrics
    └── reports/           # Daily reports & charts
```

## ⚙️ Configuration Options

Key settings in `config.py`:

```python
# Trading Settings
SYMBOL = 'IBIT'
POSITION_SIZE_PCT = 0.95  # Use 95% of buying power
MAX_POSITION_SIZE = 10000  # Max $10K per trade

# Risk Management  
MAX_DAILY_LOSS = 0.05     # Stop at 5% daily loss
MAX_TOTAL_DRAWDOWN = 0.20 # Stop at 20% total drawdown

# Schedule (Eastern Time)
MARKET_CLOSE_HOUR = 16    # 4:00 PM - buy time
MARKET_OPEN_HOUR = 9      # 9:30 AM - sell time
MARKET_OPEN_MINUTE = 30
```

## 📊 Monitoring & Reporting

### Real-time Logs
All trading activity is logged to:
- Console output
- Daily log files in `logs/`
- Trade history in `results/live_trades.json`

### Performance Metrics
- Total P&L and returns
- Win rate and trade statistics  
- Risk metrics (Sharpe ratio, volatility)
- Consecutive wins/losses
- Daily performance charts

### Sample Output
```
🚀 IBIT Overnight Strategy - Paper Trading
Symbol: IBIT
Position Size: 95% of buying power
📅 Starting trading scheduler...
✅ Scheduler configured:
   - Buy signals: Weekdays at 16:00
   - Sell signals: Weekdays at 09:30

🛒 Executing BUY signal at market close
Target: 45 shares at ~$28.50
✅ Buy order completed successfully

🔄 Executing SELL signal at market open  
Selling: 45 shares at ~$29.10
✅ Sell order completed: P&L $27.00
```

## 🔒 Risk Management

Built-in safety features:
- **Position limits**: Max position size and percentage caps
- **Daily loss limits**: Automatic stop if daily loss exceeds threshold
- **Order validation**: Double-check orders before submission
- **Market status checks**: Only trade when markets are open
- **Manual override**: Ctrl+C to stop strategy immediately

## 🧪 Testing Mode

For testing without real orders:
```python
# In config.py
DRY_RUN_MODE = True  # Simulate orders without execution
VALIDATE_ORDERS = True  # Enable order validation
```

## 📈 Expected Performance

Based on backtesting results:
- **Annual Return**: ~72% 
- **Sharpe Ratio**: ~1.8
- **Win Rate**: ~55%
- **Max Drawdown**: ~20%

Paper trading results may vary due to:
- Market conditions
- Execution timing differences
- Slippage and fills

## 🚨 Important Notes

- **Paper Trading Only**: This implementation uses Alpaca's paper trading environment
- **No Real Money**: All trades are simulated with virtual funds
- **Educational Purpose**: For testing and validation before live implementation
- **Risk Warning**: Trading involves risk of loss. Past performance doesn't guarantee future results.

## 🛡️ Safety Features

- Automatic order cancellation on shutdown
- Risk limit monitoring  
- Comprehensive logging and audit trail
- Position size validation
- Market hours verification

## 📞 Support

If you encounter issues:
1. Check `logs/` for detailed error messages
2. Run `python setup.py` to validate configuration
3. Verify Alpaca API credentials and permissions
4. Ensure market is open for trading tests

---

**Ready to start paper trading your IBIT overnight strategy!** 🚀📈