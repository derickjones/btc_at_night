# IBIT Overnight Trading Strategy# IBIT Overnight Trading Strategy# IBIT Overnight Trading Strategy# IBIT Overnight Trading Strategy - Live Automated Trading System



Automated trading system that captures Bitcoin's overnight effect via IBIT ETF. Buys at market close, sells at market open.



## 🟢 Live StatusAn automated trading system that exploits the overnight effect in IBIT (iShares Bitcoin Trust ETF). The strategy buys at market close and sells at market open, capturing Bitcoin's tendency to appreciate during overnight hours.



Two strategies running on Alpaca Paper Trading via GitHub Actions:



| Strategy | Logic | Backtest Return | Sharpe |## 🚀 Live Trading StatusAn automated trading system that exploits the overnight effect in IBIT (iShares Bitcoin Trust ETF). The strategy buys at market close and sells at market open, capturing Bitcoin's tendency to appreciate during overnight hours.A complete algorithmic trading system for IBIT (iShares Bitcoin Trust) overnight strategy. **Currently LIVE and trading automatically** via GitHub Actions cloud infrastructure with 183.8% backtested returns and 1.81 Sharpe ratio.

|----------|-------|-----------------|--------|

| **Baseline** (`live_trading/`) | Always buy overnight | 16.7% | 0.92 |

| **ML-Enhanced** (`ml_live_trading/`) | Model decides to buy/skip | **29.7%** | **2.26** |

**🟢 SYSTEM STATUS: OPERATIONAL**

**Schedule** (Mon-Fri):

- 9:31 AM EST → Sell

- 3:50 PM EST → Buy decision

| Strategy | Platform | Account | Status |## 🚀 Live Trading Status## 🤖 Live Trading Status

## 📁 Structure

|----------|----------|---------|--------|

```

btc_at_night/| **Baseline** | Alpaca Paper Trading | Account #1 | 🟢 Live |

├── live_trading/        # Baseline strategy (always trades)

├── ml_live_trading/     # ML strategy (selective trading)| **ML-Enhanced** | Alpaca Paper Trading | Account #2 | 🟢 Live |

├── ml_testing/          # ML research & backtests

└── backtesting/         # Original strategy analysis**🟢 SYSTEM STATUS: OPERATIONAL****🟢 SYSTEM STATUS: OPERATIONAL**

```

Both strategies run automatically via GitHub Actions:

## 🤖 ML Strategy

- **9:31 AM EST**: Sell signal execution

Uses 40+ features available at 3:50 PM:

- **Intraday**: Today's gap, return, IBIT vs SPY performance- **3:50 PM EST**: Buy signal execution

- **Prior-day**: Recent overnight returns, volatility, momentum

- **Calendar**: Day of week, month effects- **5:30 PM EST**: Daily email reports (baseline only)| Component | Status |- **Trading Environment**: Alpaca Paper Trading ($20,000 buying power)



Model: Logistic Regression → trades ~50-60% of nights



## 🔧 Setup## 📊 Strategy Comparison|-----------|--------|- **Execution Platform**: GitHub Actions (Free cloud hosting)



GitHub Secrets needed:

- `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` (baseline)

- `ML_ALPACA_API_KEY` / `ML_ALPACA_SECRET_KEY` (ML)### Backtested Performance (Jan 2024 - Dec 2025)| Trading Platform | Alpaca Paper Trading |- **Schedule**: 



## 📊 Monitor



- [Baseline Actions](https://github.com/derickjones/btc_at_night/actions/workflows/trading.yml)| Strategy | Total Return | Sharpe Ratio | Max Drawdown | Win Rate || Execution | GitHub Actions (automated) |  - 9:31 AM EST: Sell signal execution

- [ML Actions](https://github.com/derickjones/btc_at_night/actions/workflows/ml_trading.yml)

|----------|--------------|--------------|--------------|----------|

---

*Paper trading only. Not financial advice.*| **ML Intraday (LR)** | **29.7%** | **2.26** | -9.5% | ~55% || Buy Signal | 3:50 PM EST (weekdays) |  - 3:50 PM EST: Buy signal execution  


| ML Intraday (RF) | 24.3% | 1.67 | -10.4% | ~53% |

| Baseline (Always Night) | 16.7% | 0.92 | -12.1% | ~55% || Sell Signal | 9:31 AM EST (weekdays) |  - 5:30 PM EST: Daily email reports

| Buy & Hold IBIT | -17.1% | -0.85 | -32.7% | - |

| Daily Reports | 5:30 PM EST (email) |- **Email Reports**: Automated daily performance summaries

### Key Insight

The ML strategy with intraday features outperforms the baseline by **~75%** while having **better risk-adjusted returns** (2.26 vs 0.92 Sharpe). Both strategies significantly outperform buy & hold.- **Data Persistence**: Trade history and performance tracking



## 🤖 Strategy Versions## 📊 Backtested Performance (Jan 2024 - Dec 2025)- **Next Trade**: December 18, 2025 at 3:50 PM EST (first buy)



### 1. Baseline Strategy (`live_trading/`)

- **Logic**: Always buy at close, sell at open

- **Features**: None (pure overnight effect)| Metric | Night Strategy | Buy & Hold | Day Only |### 🔴 Live Paper Trading Features

- **Execution**: Every trading day

|--------|---------------|------------|----------|- ✅ **Fully Automated**: No manual intervention required

### 2. ML-Enhanced Strategy (`ml_live_trading/`)

- **Logic**: ML model decides whether to buy| **Total Return** | **241.8%** | 88.1% | -44.9% |- ✅ **Cloud Hosted**: Free GitHub Actions execution

- **Features**: 40+ intraday features including:

  - Today's gap (open vs yesterday's close)| **Annualized Return** | **88.6%** | 38.6% | -26.5% |- ✅ **Risk Management**: Position limits and safety controls

  - Intraday return (current price vs today's open)

  - IBIT vs SPY relative performance| **Sharpe Ratio** | **2.16** | 0.66 | -0.94 |- ✅ **Email Reporting**: Daily performance charts and summaries

  - Volume patterns

  - Prior overnight returns| **Max Drawdown** | **-20.4%** | -32.7% | -50.4% |- ✅ **Data Tracking**: Persistent trade history and metrics

  - Calendar effects

- **Execution**: Selective (~50-60% of nights)| **Win Rate** | **54.9%** | 49.2% | 48.4% |- ✅ **GitHub Integration**: Automated repository updates

- **Model**: Logistic Regression (best performer)



## 📁 Project Structure

### Key Insight## 🚀 Strategy Overview

```

btc_at_night/The night strategy outperforms buy & hold by **~3x** while having **lower drawdowns** and **better risk-adjusted returns**. Day-only trading actually *loses* money, demonstrating that nearly all of Bitcoin's gains occur overnight.

├── .github/workflows/

│   ├── trading.yml              # Baseline strategy automationThe **IBIT Overnight Trading Strategy** capitalizes on Bitcoin market inefficiencies by:

│   └── ml_trading.yml           # ML strategy automation

│## 📁 Project Structure- **Buying IBIT at market close** each trading day

├── backtesting/                 # Historical analysis

│   ├── ibit_strategy_analysis.py- **Selling IBIT at market open** the following day

│   └── output/                  # Reports and charts

│```- Capturing overnight price movements in Bitcoin-related assets

├── live_trading/                # 🟢 BASELINE STRATEGY (LIVE)

│   ├── strategy.py              # Trading logicbtc_at_night/- Generating alpha through systematic overnight exposure

│   ├── github_trading.py        # GitHub Actions adapter

│   ├── alpaca_client.py         # Alpaca API client├── .github/workflows/

│   ├── daily_email_report.py    # Email reports

│   ├── config.py                # Configuration│   └── trading.yml              # GitHub Actions automation### 📊 Key Performance Metrics

│   ├── logs/                    # Trading logs

│   └── results/                 # Trade history├── backtesting/- **Total Return**: 183.8% over ~1.92 years

│

├── ml_live_trading/             # 🟢 ML STRATEGY (LIVE)│   ├── ibit_strategy_analysis.py   # Backtest analysis script- **Annualized Return**: 72.3%

│   ├── ml_strategy.py           # ML model + trading logic

│   ├── github_trading.py        # GitHub Actions adapter│   ├── requirements.txt- **Sharpe Ratio**: 1.81 (excellent risk-adjusted returns)

│   ├── alpaca_client.py         # Alpaca API client (IEX feed)

│   ├── config.py                # Configuration│   └── output/                     # Analysis results- **Win Rate**: 54.7% across 481 trades

│   ├── models/                  # Trained ML models

│   ├── logs/                    # Trading logs│       ├── ibit_strategy_report.pdf   # Full PDF report- **Maximum Drawdown**: -20.4%

│   └── results/                 # Trade history + predictions

││       ├── cumulative_performance.png- **Volatility**: 38.8% (annualized)

├── ml_testing/                  # ML model development

│   ├── ml_strategy_analysis.py  # Baseline ML (EOD features)│       ├── monthly_returns.png

│   ├── ml_strategy_tradeable.py # Prior-day features only

│   ├── ml_strategy_intraday.py  # Intraday features (deployed)│       ├── monthly_cumulative.png## 🏗️ Project Structure

│   ├── output/                  # Baseline ML results

│   ├── output_tradeable/        # Tradeable model results│       ├── drawdowns.png

│   └── output_intraday/         # Intraday model results

││       └── return_distribution.png```

└── README.md

```├── live_trading/├── .github/workflows/



## 🔧 Setup│   ├── strategy.py              # Trading strategy logic│   └── trading.yml           # 🤖 Live trading automation (ACTIVE)



### For Baseline Strategy (already configured)│   ├── github_trading.py        # GitHub Actions adapterbacktesting/                  # Historical analysis system

The baseline strategy is already running with your original Alpaca account.

│   ├── alpaca_client.py         # Alpaca API client├── main.py                   # Main entry point for backtesting

### For ML Strategy

1. **GitHub Secrets** (already added):│   ├── monitor.py               # Performance monitoring├── core/                     # Core trading logic and utilities

   - `ML_ALPACA_API_KEY`

   - `ML_ALPACA_SECRET_KEY`│   ├── daily_email_report.py    # Email reports│   ├── data_fetcher.py      # IBIT data retrieval and management



2. **Workflow**: `.github/workflows/ml_trading.yml` is active│   ├── config.py                # Configuration│   ├── strategy.py          # Backtesting strategy implementation



### Local Development│   ├── test_trade.py            # Manual testing script│   ├── backtester.py        # Backtesting engine

```bash

# Clone repository│   ├── requirements.txt│   └── config.py            # Configuration and constants

git clone https://github.com/derickjones/btc_at_night.git

cd btc_at_night│   ├── logs/                    # Trading logs├── analysis/                 # Analysis and reporting tools



# Create virtual environment│   └── results/                 # Trade history├── monitoring/              # Performance monitoring system

python -m venv .venv

source .venv/bin/activate└── README.md├── data/                    # Raw historical data



# Install dependencies```├── results/                 # Analysis results and reports

pip install -r live_trading/requirements.txt

pip install -r ml_live_trading/requirements.txt│   └── IBIT_Strategy_Complete_Analysis.pdf # Comprehensive report



# Test ML strategy locally## 🔧 Setup└── docs/                    # Documentation

cd ml_live_trading

python ml_strategy.py

```

### 1. Clone Repositorylive_trading/                 # 🟢 LIVE TRADING SYSTEM (OPERATIONAL)

## 📈 ML Model Features

```bash├── strategy.py              # 🤖 Live trading strategy (ACTIVE)

The ML strategy uses features available at 3:50 PM EST:

git clone https://github.com/derickjones/btc_at_night.git├── github_trading.py        # GitHub Actions adapter

### Same-Day Intraday Features

| Feature | Description |cd btc_at_night├── alpaca_client.py         # Alpaca API integration

|---------|-------------|

| `today_gap` | Gap from yesterday's close to today's open |```├── daily_email_report.py    # 📧 Email reporting system

| `intraday_return` | Return from today's open to current price |

| `intraday_vs_spy` | IBIT performance relative to SPY today |├── monitor.py               # Performance monitoring

| `intraday_range` | Today's high-low range (volatility) |

| `intraday_position` | Where current price is in today's range |### 2. Create Virtual Environment├── config.py                # Live trading configuration  

| `today_volume_vs_ma` | Today's volume vs recent average |

```bash├── setup.py                 # System validation

### Prior-Day Features

| Feature | Description |python -m venv .venv├── data/                    # Live trading data

|---------|-------------|

| `prev_overnight_*` | Recent overnight returns (1, 2, 3, 5-day avg) |source .venv/bin/activate  # macOS/Linux├── logs/                    # 📝 Trading activity logs

| `prior_*d_return` | Returns over past 1/5/10/20 days |

| `ibit_vs_spy_*` | IBIT relative strength vs SPY |# or: .venv\Scripts\activate  # Windows└── results/                 # 📊 Live trading performance data

| `prior_volatility_*` | Recent volatility measures |

``````

### Calendar Features

- Day of week, month, quarter

- Month start/end indicators

- Monday/Friday effects### 3. Install Dependencies## � Live Trading Quick Start



## 📊 Monitoring```bash



### GitHub Actionspip install -r live_trading/requirements.txt### System is Already Running! 🎉

- **Baseline**: https://github.com/derickjones/btc_at_night/actions/workflows/trading.yml

- **ML**: https://github.com/derickjones/btc_at_night/actions/workflows/ml_trading.ymlpip install -r backtesting/requirements.txtThe strategy is **automatically trading** via GitHub Actions. No setup required!



### Trade History```

- Baseline: `live_trading/results/live_trades.json`

- ML: `ml_live_trading/results/ml_live_trades.json`- **View Live Status**: Check the [GitHub Actions page](https://github.com/derickjones/btc_at_night/actions)



### ML Predictions### 4. Configure Alpaca API- **Monitor Performance**: Daily email reports sent to configured address

- All predictions (buy & skip): `ml_live_trading/results/ml_predictions.json`

Edit `live_trading/config.py` with your Alpaca paper trading credentials:- **Trade History**: Automatically updated in `live_trading/results/`

## 🔬 Research & Analysis

```python

The `ml_testing/` folder contains the research that led to the ML strategy:

ALPACA_API_KEY = 'your_api_key'### 📧 Email Report Schedule

1. **Baseline ML** (`ml_strategy_analysis.py`): Used end-of-day features (not tradeable - data unavailable at decision time)

ALPACA_SECRET_KEY = 'your_secret_key'- **5:30 PM EST Daily**: Performance summary, charts, trade details

2. **Tradeable Model** (`ml_strategy_tradeable.py`): Prior-day features only - 21.9% return, 1.44 Sharpe

```- **First Report**: December 18, 2025 (after first trade execution)

3. **Intraday Model** (`ml_strategy_intraday.py`): Same-day features available at 3:50 PM - **29.7% return, 2.26 Sharpe** ✅



Each folder contains PDF reports with SHAP analysis showing feature importance.

### 5. Configure GitHub Secrets (for automated trading)### 🔧 Local Development Setup (Optional)

## 📝 License

Add these secrets to your GitHub repository:

MIT License - Feel free to use and modify.

- `ALPACA_API_KEY````bash

## ⚠️ Disclaimer

- `ALPACA_SECRET_KEY`# Clone the repository

This is for educational and paper trading purposes. Past performance does not guarantee future results. Always do your own research before trading with real money.

- `EMAIL_APP_PASSWORD` (Gmail app password for reports)git clone https://github.com/derickjones/btc_at_night.git

cd btc_at_night

## 📈 Running the Backtest

# Setup virtual environment

```bashpython -m venv .venv

cd backtestingsource .venv/bin/activate

python ibit_strategy_analysis.py

```# Install dependencies

pip install -r live_trading/requirements.txt

This generates:

- Performance metrics comparison# Test local execution (optional)

- Monthly returns analysiscd live_trading && python setup.py

- PDF report with all charts```

- CSV data files

## 🚀 Backtesting Analysis

## 🧪 Testing Live Trading

The project provides comprehensive backtesting capabilities through `main.py`:

```bash

cd live_trading### Available Commands

python test_trade.py

``````bash

cd backtesting

This verifies:

- Alpaca API connectivity# Run comprehensive strategy analysis

- Account status and buying powerpython main.py analyze

- Current positions

- Market data access# Update data and run monthly analysis

- Order execution (when market is open)python main.py update



## 🤖 GitHub Actions Automation# Generate PDF performance report

python main.py report

The workflow runs automatically on weekdays:

# Run performance monitoring

| Time (EST) | Action |python main.py monitor

|------------|--------|

| 9:31 AM | Execute sell signal (close overnight position) |# Show help

| 3:50 PM | Execute buy signal (open overnight position) |python main.py --help

| 5:30 PM | Send daily email report |```



To manually trigger: Go to Actions → "IBIT Overnight Trading Strategy" → "Run workflow"### Example Usage



## 📧 Email Reports```bash

# Generate the latest performance report

Daily reports include:cd backtesting

- Performance summarypython main.py report

- Current position

- P&L tracking# This creates: results/IBIT_Strategy_Complete_Analysis.pdf

- Trade history# - 4.8MB comprehensive report

# - 6 professional charts and graphs

Configure in `live_trading/config.py`:# - Detailed performance analysis

```python# - Risk metrics and implementation guidance

EMAIL_FROM = 'your_email@gmail.com'```

EMAIL_RECIPIENTS = ['recipient@email.com']

EMAIL_APP_PASSWORD = 'your_gmail_app_password'## 🤖 Live Trading Architecture

```

### GitHub Actions Automation

## ⚠️ Disclaimer```yaml

# .github/workflows/trading.yml

This project is for **educational purposes only**. schedule:

  - cron: '31 14 * * 1-5'  # 9:31 AM EST (Sell)

- Past performance does not guarantee future results  - cron: '50 20 * * 1-5'  # 3:50 PM EST (Buy)  

- Trading involves risk of loss  - cron: '30 22 * * 1-5'  # 5:30 PM EST (Email Report)

- Currently configured for **paper trading only**```

- Do your own research before trading with real money

### Trading Flow

## 📄 License1. **Market Open (9:31 AM)**: Sell overnight position

2. **Market Close (3:50 PM)**: Buy new position for overnight hold

MIT License - See LICENSE file for details.3. **Evening (5:30 PM)**: Generate and email daily performance report

4. **Data Persistence**: All trades saved to GitHub repository

---5. **Error Handling**: Comprehensive logging and email notifications



**Status**: 🟢 Live | **Next Trade**: When market opens | **Platform**: Alpaca Paper Trading# Generate PDF performance report

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