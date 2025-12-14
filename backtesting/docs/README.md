# IBIT Overnight Trading Strategy Backtester

A Python project for backtesting a trading strategy that buys IBIT (iShares Bitcoin Trust ETF) at market close and sells at market open the next day.

## Strategy Overview

- **Entry**: Buy IBIT at market close (4:00 PM ET)
- **Exit**: Sell IBIT at market open (9:30 AM ET next trading day)
- **Hypothesis**: Bitcoin tends to move overnight, potentially providing positive returns for this overnight holding strategy

## Project Structure

```
btc_at_night/
├── src/
│   ├── data_fetcher.py      # Data collection and processing
│   ├── strategy.py          # Trading strategy implementation
│   ├── backtester.py        # Backtesting engine
│   └── visualization.py     # Results visualization
├── data/                    # Raw and processed data
├── tests/                   # Unit tests
├── results/                 # Backtest results and charts
├── config.py                # Configuration parameters
├── main.py                  # Main execution script
└── requirements.txt         # Python dependencies
```

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Configuration

Edit `config.py` to adjust:
- Backtesting date range
- Initial capital
- Transaction costs
- Other parameters

## Results

Results will be saved in the `results/` directory including:
- Performance charts
- Statistics summary
- Trade log