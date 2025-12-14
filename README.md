# IBIT Overnight Trading Strategy - Backtesting Suite

A comprehensive backtesting and monitoring system for an IBIT (iShares Bitcoin Trust) overnight trading strategy that demonstrates exceptional performance with 183.8% total returns and a 1.81 Sharpe ratio.

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
backtesting/
├── main.py                    # Main entry point for all operations
├── core/                      # Core trading logic and utilities
│   ├── data_fetcher.py       # IBIT data retrieval and management
│   ├── strategy.py           # Trading strategy implementation
│   ├── backtester.py         # Backtesting engine
│   └── config.py             # Configuration and constants
├── analysis/                  # Analysis and reporting tools
│   ├── analyze.py            # Core strategy analysis
│   ├── create_combined_pdf.py # PDF report generation
│   ├── analyze_ibit_spy_strategy.py # SPY enhancement analysis
│   └── strategy_comparison.py # Strategy comparison tools
├── monitoring/               # Performance monitoring system
│   ├── monthly_update.py     # Monthly data updates
│   ├── monthly_monitor.py    # Performance monitoring
│   └── run_monthly_update.py # Update orchestration
├── data/                     # Raw data storage
├── results/                  # Analysis results and reports
│   ├── IBIT_Strategy_Complete_Analysis.pdf # Comprehensive PDF report
│   ├── trade_results.csv     # Individual trade results
│   ├── performance_summary.csv # Key performance metrics
│   ├── rolling_metrics.csv   # Rolling performance analysis
│   └── pdf_charts/          # Generated charts for reports
├── docs/                     # Documentation
└── scripts/                  # Utility scripts
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.12+
- Virtual environment (recommended)

### Setup Instructions

1. **Clone and navigate to the project:**
   ```bash
   cd btc_at_night/backtesting
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```

3. **Install required packages:**
   ```bash
   pip install pandas numpy matplotlib yfinance reportlab seaborn
   ```

## 🚀 Quick Start

The project provides a unified command-line interface through `main.py`:

### Available Commands

```bash
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
python main.py report

# This creates: results/IBIT_Strategy_Complete_Analysis.pdf
# - 4.8MB comprehensive report
# - 6 professional charts and graphs
# - Detailed performance analysis
# - Risk metrics and implementation guidance
```

## 📈 Strategy Performance

### Core IBIT Overnight Strategy
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

## ⚠️ Risk Considerations

- **High Volatility**: 38.8% annual volatility requires risk tolerance
- **Drawdown Exposure**: -20.4% maximum drawdown periods
- **Market Dependency**: Performance tied to Bitcoin/crypto conditions
- **Pattern Decay**: Overnight inefficiencies may diminish over time

## 🎯 Implementation Readiness

### Alpaca Trading Integration
- ✅ Commission-free trading assumption validated
- ✅ Realistic 0.01% slippage modeling
- ✅ Systematic entry/exit rules established
- ✅ Strong backtested performance verified
- ✅ Manageable drawdown characteristics

### Recommended Implementation Steps
1. Start with smaller position sizes for live validation
2. Implement automated execution via Alpaca API
3. Monitor performance vs. backtested expectations
4. Use volatility-based position sizing during stress
5. Set stop-loss rules if drawdowns exceed tolerance

## 📚 Files Reference

### Core Data Files
- `trade_results.csv` - Individual trade details and P&L
- `performance_summary.csv` - Aggregated performance metrics
- `rolling_metrics.csv` - 30-day rolling performance windows
- `ibit_spy_combined_strategy.csv` - Enhanced strategy results

### Key Scripts
- `main.py` - Central command interface
- `analyze.py` - Core backtesting analysis
- `create_combined_pdf.py` - Professional report generation
- `monthly_update.py` - Automated data updates

## 🤝 Contributing

To extend or modify the strategy:

1. Core strategy logic: `backtesting/core/strategy.py`
2. Analysis methods: `backtesting/analysis/`
3. Monitoring systems: `backtesting/monitoring/`
4. Add new charts: `backtesting/results/pdf_charts/`

## 📄 License

This project is for educational and research purposes. Trading involves risk of loss. Past performance does not guarantee future results.

## ⚡ Key Features

- **Comprehensive Backtesting**: Full historical analysis with realistic costs
- **Professional Reporting**: Publication-quality PDF reports with charts
- **Automated Updates**: Monthly data refresh and analysis pipeline
- **Risk Management**: Detailed drawdown and volatility analysis
- **Strategy Enhancement**: SPY day-trading combination analysis
- **Implementation Ready**: Alpaca-compatible execution framework

---

**Generated by IBIT Backtesting Suite** | Last Updated: December 2025