# IBIT Overnight Trading Strategy - Monthly Monitoring System

## Overview

This monitoring system tracks the performance of the IBIT overnight trading strategy on a monthly basis to detect edge persistence and performance degradation. The core strategy buys IBIT at market close and sells at market open, targeting the overnight premium.

## Strategy Summary

**Core Strategy Performance (Baseline):**
- Annual Return: 72.3%
- Sharpe Ratio: 1.81
- Win Rate: 54.7%
- Max Drawdown: -20.4%

**Enhanced Strategy (with SPY day trading):**
- Annual Return: 79.2% (+6.9% enhancement)
- Utilizes capital during market hours with SPY day trading

## Monitoring Components

### 1. Monthly Performance Monitor (`monthly_monitor.py`)
- **Purpose**: Core monthly analysis engine
- **Function**: Compares recent performance against baseline metrics
- **Analysis**: 90-day rolling performance, trade patterns, performance flags
- **Output**: Detailed monthly report with executive summary

### 2. Historical Tracker (`historical_tracker.py`)
- **Purpose**: Long-term trend analysis and edge persistence tracking
- **Function**: Maintains historical performance database
- **Analysis**: Multi-month trends, edge persistence rates, consistency metrics
- **Output**: Historical dashboard, trend analysis, edge persistence report

### 3. Monthly Check Script (`run_monthly_check.py`)
- **Purpose**: Complete monitoring workflow execution
- **Function**: Orchestrates monthly analysis and historical tracking
- **Usage**: Run monthly to maintain edge monitoring
- **Output**: Executive summary, detailed reports, performance charts

## Key Monitoring Metrics

### Performance Tracking
- **Annual Return**: Target >70% (baseline: 72.3%)
- **Sharpe Ratio**: Target >1.5 (baseline: 1.81)
- **Win Rate**: Target >50% (baseline: 54.7%)
- **Max Drawdown**: Monitor for increases above -25%

### Edge Persistence
- **Persistence Rate**: % of months outperforming baseline
- **Consistency Score**: % of months within 2% of baseline
- **Performance Volatility**: Standard deviation of monthly returns

### Alert Conditions
- Return drops >10% below baseline
- Sharpe ratio falls below 1.0
- Win rate drops below 45%
- Max drawdown exceeds -30%
- 3+ consecutive months underperforming

## Usage Instructions

### Monthly Monitoring (Recommended)
```bash
python run_monthly_check.py
```

### Manual Analysis
```python
from monthly_monitor import run_monthly_monitoring
results = run_monthly_monitoring()
```

### Historical Analysis Only
```python
from historical_tracker import run_historical_analysis
run_historical_analysis()
```

## Output Files

### Monthly Reports
- **Location**: `results/monthly_monitoring/`
- **Files**:
  - `monthly_report_YYYY-MM-DD.json` - Detailed analysis
  - `performance_chart_YYYY-MM-DD.png` - Visual performance summary
  - `historical_dashboard_YYYY-MM-DD.png` - Multi-month trends

### Historical Database
- **File**: `results/monthly_monitoring/performance_history.csv`
- **Content**: Month-by-month performance metrics
- **Use**: Trend analysis and edge persistence tracking

## Performance Interpretation

### Strong Edge (🟢)
- Edge Persistence Rate >70%
- Consistent outperformance vs baseline
- Stable Sharpe ratio trends
- Few performance flags

### Moderate Edge (🟡)
- Edge Persistence Rate 50-70%
- Occasional underperformance
- Some performance volatility
- Monitor for degradation

### Weak Edge (🔴)
- Edge Persistence Rate <50%
- Frequent underperformance
- High performance volatility
- Multiple performance flags

### Immediate Actions Required
- Edge Persistence Rate <30%
- 3+ consecutive months underperforming
- Sharpe ratio trending below 1.0
- Strategy modifications may be needed

## Dependencies

```bash
pip install yfinance pandas numpy matplotlib seaborn reportlab
```

## Integration with Trading

The monitoring system is designed to:
1. **Detect edge degradation early** - Before significant losses
2. **Validate strategy persistence** - Ensure overnight premium continues
3. **Guide position sizing** - Adjust based on recent performance
4. **Inform strategy evolution** - Identify improvement opportunities

## Recommended Schedule

- **Weekly**: Review performance flags and recent trades
- **Monthly**: Run complete monitoring analysis
- **Quarterly**: Deep dive into historical trends
- **Annually**: Strategy review and optimization

## Troubleshooting

### Common Issues
1. **Data fetch failures**: Check yfinance connectivity
2. **Missing historical data**: Accumulates over time, requires 2+ months for trends
3. **Performance calculation errors**: Verify IBIT trading hours and market calendars

### Data Quality
- Uses official IBIT ETF data from Yahoo Finance
- Handles market holidays and trading gaps
- Validates data completeness before analysis

## Next Steps

As you build monitoring history:
1. **Month 1-3**: Establish baseline tracking
2. **Month 4-6**: Begin trend analysis
3. **Month 6+**: Full edge persistence evaluation
4. **Month 12+**: Annual performance review and strategy optimization

The system is designed to evolve with your strategy monitoring needs while maintaining focus on the core question: **Does the IBIT overnight edge persist?**