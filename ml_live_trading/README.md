# ML Live Trading - IBIT Overnight Strategy

Machine learning enhanced version of the IBIT overnight trading strategy.

## Overview

This strategy uses an ML model trained on intraday features (available at 3:50 PM EST) to decide whether to buy IBIT before market close. The model predicts the probability of a positive overnight return and only buys when the probability exceeds the configured threshold.

### Key Difference from Baseline Strategy

| Feature | Baseline (`live_trading/`) | ML Strategy (`ml_live_trading/`) |
|---------|---------------------------|----------------------------------|
| Decision Logic | Always buy at close | ML model decides |
| Features Used | None | 40+ intraday features |
| Expected Selectivity | Trades every night | Trades ~50-60% of nights |
| Backtest Return | 16.7% | 29.7% (Logistic Regression) |
| Backtest Sharpe | 0.92 | 2.26 |

## Setup

### 1. Alpaca Account

This uses a **separate** Alpaca paper trading account from the baseline strategy:
- API Key: `PK5CVE3IJVB5LJP3AB5LRXBCXF`
- Base URL: `https://paper-api.alpaca.markets/v2`

### 2. Install Dependencies

```bash
cd ml_live_trading
pip install -r requirements.txt
```

### 3. Test Locally

```bash
# Test ML prediction (won't execute trades)
python ml_strategy.py

# Test full trading cycle
python github_trading.py
```

## Files

| File | Purpose |
|------|---------|
| `config.py` | Configuration (API keys, thresholds, trading times) |
| `alpaca_client.py` | Alpaca API client with intraday data methods |
| `ml_strategy.py` | ML model training, prediction, and trade execution |
| `github_trading.py` | GitHub Actions adapter for scheduled execution |

## Configuration

Key settings in `config.py`:

```python
# ML Model Settings
ML_BUY_THRESHOLD = 0.5  # Buy when probability > 50%
ML_MODEL_TYPE = 'logistic_regression'  # Best performer

# Trading Schedule (EST)
MARKET_CLOSE_HOUR = 15   # 3:50 PM - buy decision
MARKET_CLOSE_MINUTE = 50
MARKET_OPEN_HOUR = 9     # 9:40 AM - sell
MARKET_OPEN_MINUTE = 40
```

## ML Model Features

The model uses features available at 3:50 PM EST:

### Same-Day Intraday Features
- `today_gap`: Gap from yesterday's close to today's open
- `intraday_return`: Today's return so far (open to current)
- `intraday_vs_spy`: IBIT vs SPY intraday performance
- `intraday_range`: Today's high-low range
- `intraday_position`: Where current price is in today's range
- `today_volume_vs_ma`: Today's volume vs recent average

### Prior-Day Features
- `prev_overnight_*`: Recent overnight returns
- `prior_*d_return`: Returns over past 1/5/10/20 days
- `prior_volatility_*`: Recent volatility measures
- `*_vs_ma*`: Price relative to moving averages

### Calendar Features
- Day of week, month, quarter
- Month start/end indicators

## GitHub Actions Setup

Add these secrets to your repository:
- `ML_ALPACA_API_KEY`
- `ML_ALPACA_SECRET_KEY`

Create `.github/workflows/ml_trading.yml`:

```yaml
name: ML IBIT Trading

on:
  schedule:
    # Buy signal: 3:50 PM EST (20:50 UTC)
    - cron: '50 20 * * 1-5'
    # Sell signal: 9:40 AM EST (14:40 UTC)
    - cron: '40 14 * * 1-5'
  workflow_dispatch:

jobs:
  trade:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r ml_live_trading/requirements.txt
      
      - name: Run ML Trading
        env:
          ML_ALPACA_API_KEY: ${{ secrets.ML_ALPACA_API_KEY }}
          ML_ALPACA_SECRET_KEY: ${{ secrets.ML_ALPACA_SECRET_KEY }}
        run: |
          cd ml_live_trading
          python github_trading.py
```

## Output Files

Results are stored in:
- `results/ml_live_trades.json` - Trade history
- `results/ml_predictions.json` - All ML predictions (buy & skip)
- `results/ml_live_performance.json` - Performance metrics
- `logs/ml_strategy_*.log` - Daily log files
- `models/` - Trained model files (auto-generated)

## Monitoring

Check prediction history:
```bash
cat results/ml_predictions.json | python -m json.tool
```

Check performance:
```bash
cat results/ml_live_performance.json | python -m json.tool
```

## Model Retraining

The model auto-trains on first run and saves to `models/`. To retrain:

```bash
rm models/*.pkl
python ml_strategy.py
```

## Comparison with Baseline

Run both strategies in parallel:
- **Baseline** (`live_trading/`): Always trades, uses first Alpaca account
- **ML** (`ml_live_trading/`): Selective trading, uses second Alpaca account

After a few weeks, compare performance to validate ML improvement.
