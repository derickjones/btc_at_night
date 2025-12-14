# IBIT Backtesting Suite

A comprehensive backtesting and monitoring system for IBIT overnight trading strategy.

## 📁 Project Structure

```
backtesting/
├── main.py                 # Main entry point
├── core/                   # Core strategy implementation
│   ├── strategy.py         # IBIT overnight strategy
│   ├── backtester.py       # Backtesting engine
│   ├── data_fetcher.py     # Market data fetching
│   ├── visualization.py    # Charts and plotting
│   └── config.py           # Configuration settings
├── analysis/               # Analysis scripts
│   ├── analyze.py          # Main analysis script
│   ├── analyze_ibit_spy_strategy.py  # SPY enhancement
│   ├── strategy_comparison.py        # Strategy comparisons
│   └── create_combined_pdf.py       # PDF report generator
├── monitoring/             # Monitoring and automation
│   ├── run_monthly_update.py        # Main update script
│   ├── monthly_update.py            # Update orchestrator
│   ├── monthly_monitor.py           # Performance monitoring
│   └── historical_tracker.py       # Historical analysis
├── data/                   # Market data cache
├── results/                # Analysis outputs and reports
├── docs/                   # Documentation
├── scripts/                # Utility scripts
└── archive/                # Archived files
```

## 🚀 Quick Start

### Run Full Analysis
```bash
cd backtesting
python main.py analyze
```

### Monthly Update
```bash
python main.py update
```

### Generate PDF Report
```bash
python main.py report
```

### Monitor Performance
```bash
python main.py monitor
```

## 📊 Strategy Performance

- **IBIT Overnight Strategy**: 183.8% total return (72.3% annualized)
- **SPY Day Trading Enhancement**: +33.2% improvement
- **Combined Portfolio**: 205.5% total return

## 🔄 Monthly Workflow

1. **Automatic Updates**: Run `python main.py update` monthly
2. **Performance Monitoring**: Track edge persistence with rolling analysis
3. **PDF Reports**: Comprehensive analysis with visualizations
4. **Backup Management**: Automatic backup of previous results

## 📈 Key Features

- Comprehensive backtesting engine
- Risk-adjusted performance metrics
- Rolling performance analysis
- Monthly monitoring automation
- Professional PDF reporting
- SPY day trading enhancement
- Automated backup system

## ⚙️ Configuration

Edit `core/config.py` to modify:
- Initial capital
- Transaction costs
- Date ranges
- Risk parameters

## 📄 Documentation

See `docs/` folder for detailed guides:
- README.md - Main documentation
- MONITORING_README.md - Monitoring setup
- MONTHLY_UPDATE_GUIDE.md - Update procedures
- VISUAL_MONITORING_GUIDE.md - Visualization guide
