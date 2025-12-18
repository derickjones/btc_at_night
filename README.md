# IBIT Overnight Trading Strategy - Live Automated Trading System

A complete algorithmic trading system for IBIT (iShares Bitcoin Trust) overnight strategy. **Currently LIVE and trading automatically** via GitHub Actions cloud infrastructure with 183.8% backtested returns and 1.81 Sharpe ratio.

## 🤖 Live Trading Status

**🟢 SYSTEM STATUS: OPERATIONAL**

- **Trading Environment**: Alpaca Paper Trading ($20,000 buying power)
- **Execution Platform**: GitHub Actions (Free cloud hosting)
- **Schedule**: 
  - 9:40 AM EST: Sell signal execution
  - 3:50 PM EST: Buy signal execution  
  - 5:30 PM EST: Daily email reports
- **Email Reports**: Automated daily performance summaries
- **Data Persistence**: Trade history and performance tracking
- **Next Trade**: December 18, 2025 at 3:50 PM EST (first buy)

### 🔴 Live Paper Trading Features
- ✅ **Fully Automated**: No manual intervention required
- ✅ **Cloud Hosted**: Free GitHub Actions execution
- ✅ **Risk Management**: Position limits and safety controls
- ✅ **Email Reporting**: Daily performance charts and summaries
- ✅ **Data Tracking**: Persistent trade history and metrics
- ✅ **GitHub Integration**: Automated repository updates

## 🚀 Strategy Overview

The **IBIT Overnight Trading Strategy** capitalizes on Bitcoin market inefficiencies by:
- **Buying IBIT at market close** each trading day
- **Selling IBIT at market open** the following day
- Capturing overnight price movements in Bitcoin-related assets
- Generating alpha through systematic overnight exposure

### 📊 Key Performance Metrics
- **Total Return**: 183.8% over ~1.92 years
- **Annualized Return**: 72.3%
- **Sharpe Ratio**: 1.81 (excellent risk-adjusted returns)
- **Win Rate**: 54.7% across 481 trades
- **Maximum Drawdown**: -20.4%
- **Volatility**: 38.8% (annualized)

## 🏗️ Project Structure

```
├── .github/workflows/
│   └── trading.yml           # 🤖 Live trading automation (ACTIVE)
backtesting/                  # Historical analysis system
├── main.py                   # Main entry point for backtesting
├── core/                     # Core trading logic and utilities
│   ├── data_fetcher.py      # IBIT data retrieval and management
│   ├── strategy.py          # Backtesting strategy implementation
│   ├── backtester.py        # Backtesting engine
│   └── config.py            # Configuration and constants
├── analysis/                 # Analysis and reporting tools
├── monitoring/              # Performance monitoring system
├── data/                    # Raw historical data
├── results/                 # Analysis results and reports
│   └── IBIT_Strategy_Complete_Analysis.pdf # Comprehensive report
└── docs/                    # Documentation

live_trading/                 # 🟢 LIVE TRADING SYSTEM (OPERATIONAL)
├── strategy.py              # 🤖 Live trading strategy (ACTIVE)
├── github_trading.py        # GitHub Actions adapter
├── alpaca_client.py         # Alpaca API integration
├── daily_email_report.py    # 📧 Email reporting system
├── monitor.py               # Performance monitoring
├── config.py                # Live trading configuration  
├── setup.py                 # System validation
├── data/                    # Live trading data
├── logs/                    # 📝 Trading activity logs
└── results/                 # 📊 Live trading performance data
```

## � Live Trading Quick Start

### System is Already Running! 🎉
The strategy is **automatically trading** via GitHub Actions. No setup required!

- **View Live Status**: Check the [GitHub Actions page](https://github.com/derickjones/btc_at_night/actions)
- **Monitor Performance**: Daily email reports sent to configured address
- **Trade History**: Automatically updated in `live_trading/results/`

### 📧 Email Report Schedule
- **5:30 PM EST Daily**: Performance summary, charts, trade details
- **First Report**: December 18, 2025 (after first trade execution)

### 🔧 Local Development Setup (Optional)

```bash
# Clone the repository
git clone https://github.com/derickjones/btc_at_night.git
cd btc_at_night

# Setup virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r live_trading/requirements.txt

# Test local execution (optional)
cd live_trading && python setup.py
```

## 🚀 Backtesting Analysis

The project provides comprehensive backtesting capabilities through `main.py`:

### Available Commands

```bash
cd backtesting

# Run comprehensive strategy analysis
python main.py analyze

# Update data and run monthly analysis
python main.py update

# Generate PDF performance report
python main.py report

# Run performance monitoring
python main.py monitor

# Show help
python main.py --help
```

### Example Usage

```bash
# Generate the latest performance report
cd backtesting
python main.py report

# This creates: results/IBIT_Strategy_Complete_Analysis.pdf
# - 4.8MB comprehensive report
# - 6 professional charts and graphs
# - Detailed performance analysis
# - Risk metrics and implementation guidance
```

## 🤖 Live Trading Architecture

### GitHub Actions Automation
```yaml
# .github/workflows/trading.yml
schedule:
  - cron: '40 14 * * 1-5'  # 9:40 AM EST (Sell)
  - cron: '50 20 * * 1-5'  # 3:50 PM EST (Buy)  
  - cron: '30 22 * * 1-5'  # 5:30 PM EST (Email Report)
```

### Trading Flow
1. **Market Open (9:40 AM)**: Sell overnight position
2. **Market Close (3:50 PM)**: Buy new position for overnight hold
3. **Evening (5:30 PM)**: Generate and email daily performance report
4. **Data Persistence**: All trades saved to GitHub repository
5. **Error Handling**: Comprehensive logging and email notifications

# Generate PDF performance report
python main.py report

# Run performance monitoring
python main.py monitor

# Show help
python main.py --help
```

### Example Usage

```bash
# Generate the latest performance report
python main.py report

# This creates: results/IBIT_Strategy_Complete_Analysis.pdf
# - 4.8MB comprehensive report
# - 6 professional charts and graphs
# - Detailed performance analysis
# - Risk metrics and implementation guidance
```

## � Strategy Performance & Live Monitoring

### Real-Time Performance Tracking
- **Live Portfolio Value**: Updated with each trade
- **Daily P&L**: Emailed each evening at 5:30 PM EST
- **Win Rate Tracking**: Running calculation across all trades
- **Drawdown Monitoring**: Real-time risk assessment
- **Performance Charts**: Daily visualizations in email reports

### Backtested Performance (Validation Period)
- **Period**: January 2024 - December 2025
- **Total Trades**: 481
- **Success Rate**: 54.7%
- **Best Trade**: +10.56%
- **Worst Trade**: -20.40%
- **Profit Factor**: 1.33

### Enhanced SPY Combination Strategy
- **Combined Return**: 205.5% (IBIT overnight + SPY day trading)
- **IBIT Contribution**: 50.7% annual
- **SPY Contribution**: 5.0% annual
- **Diversification Benefits**: Reduced overall portfolio risk

## 📊 Report Generation

The system generates comprehensive PDF reports including:

### Charts & Visualizations
- **Portfolio Performance**: Growth trajectory over time
- **Strategy Comparison**: vs buy-and-hold alternatives
- **Returns Distribution**: Statistical analysis of outcomes
- **Drawdown Analysis**: Risk exposure periods
- **Rolling Metrics**: 30-day performance windows
- **Trend Analysis**: Long-term performance patterns

### Analysis Sections
- Executive Summary with key metrics
- Detailed performance breakdown
- Risk analysis and metrics
- Trading statistics
- Implementation recommendations
- SPY enhancement strategy results

## 🔄 Monthly Updates

Automated monthly update system:

```bash
python main.py update
```

This command:
1. Fetches latest IBIT price data
2. Runs updated backtest analysis
3. Generates fresh performance metrics
4. Updates rolling analysis windows
5. Creates backup of previous results
6. Logs update completion with timestamps

## ⚠️ Risk Management & Monitoring

### Live Risk Controls
- **Position Sizing**: Dynamic based on available buying power
- **Market Hours**: Trading only during market open periods
- **Order Validation**: Pre-trade position and balance checks
- **Error Handling**: Comprehensive logging and email alerts
- **Data Backup**: All trade data persisted to GitHub repository

### Performance Monitoring
- **Daily Email Reports**: Complete performance summary with charts
- **Real-time Logging**: All trading activity tracked and stored
- **GitHub Integration**: Automatic repository updates with trade data
- **Portfolio Tracking**: Live position and P&L monitoring

## 🎯 System Status & Next Steps

### Current Implementation ✅
- ✅ **Live Trading**: Operational via GitHub Actions
- ✅ **Alpaca Integration**: Paper trading with $20,000 buying power
- ✅ **Automated Execution**: Buy/sell signals scheduled and running
- ✅ **Email Reports**: Daily performance summaries configured
- ✅ **Data Persistence**: Trade history and performance tracking active
- ✅ **Risk Management**: Position limits and safety controls implemented

### Monitoring Your Strategy
1. **Daily Email Reports**: Automated performance summaries at 5:30 PM EST
2. **GitHub Repository**: Check for trade data updates after each execution
3. **Action Logs**: Review GitHub Actions page for execution status
4. **Performance Files**: Monitor `live_trading/results/` for trade history

## 📚 File Reference & System Components

### Live Trading Files (Active System)
- `live_trading/strategy.py` - 🤖 **Main trading logic** (LIVE)
- `live_trading/github_trading.py` - GitHub Actions adapter
- `live_trading/alpaca_client.py` - Alpaca API integration
- `live_trading/daily_email_report.py` - 📧 Email reporting system
- `live_trading/results/` - 📊 **Live performance data**
- `live_trading/logs/` - 📝 **Trading activity logs**
- `.github/workflows/trading.yml` - 🤖 **Automation workflow** (ACTIVE)

### Backtesting & Analysis Files
- `backtesting/main.py` - Central command interface for analysis
- `backtesting/results/IBIT_Strategy_Complete_Analysis.pdf` - Comprehensive report
- `trade_results.csv` - Individual trade details and P&L
- `performance_summary.csv` - Aggregated performance metrics
- `rolling_metrics.csv` - 30-day rolling performance windows

## 🤝 Contributing

To extend or modify the strategy:

1. Core strategy logic: `backtesting/core/strategy.py`
2. Analysis methods: `backtesting/analysis/`
3. Monitoring systems: `backtesting/monitoring/`
4. Add new charts: `backtesting/results/pdf_charts/`

## 📄 License

This project is for educational and research purposes. Trading involves risk of loss. Past performance does not guarantee future results.

## ⚡ Key Features

- **🤖 Fully Automated Trading**: GitHub Actions cloud execution with zero maintenance
- **📧 Daily Email Reports**: Automated performance summaries with charts and trade details
- **☁️ Free Cloud Hosting**: No server costs using GitHub Actions infrastructure
- **📊 Real-time Monitoring**: Live position tracking and performance analysis
- **🔒 Risk Management**: Comprehensive safety controls and position limits
- **📈 Proven Strategy**: 183.8% backtested returns with 1.81 Sharpe ratio
- **💾 Data Persistence**: Complete trade history and performance tracking
- **🔧 Zero Maintenance**: Fully autonomous operation requiring no intervention

---

**🚀 IBIT Overnight Trading System - LIVE & OPERATIONAL** | Next Trade: December 18, 2025 | Status: 🟢 Active