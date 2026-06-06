# Fidelity Tax Loss Harvesting - Nasdaq 100 Basket Strategy

## Overview

This project implements a **tax-optimized investment strategy** using the top 50 Nasdaq 100 stocks divided into 3 baskets, with a **SpaceX placeholder** for when SpaceX IPOs. The strategy maintains QQQ-like exposure while generating tax benefits through:

1. **Tax Loss Harvesting** - Swapping between baskets to realize losses
2. **Charitable Donations** - Donating appreciated shares for tax deductions
3. **Equal Contribution Rebalancing** - Adding $500/week to the most underweight basket

## Why Top 50 Stocks?

- The top 50 Nasdaq 100 stocks cover **~93% of QQQ's index weight**
- Renormalized to 100%, they provide nearly identical exposure to the full index
- Fewer tickers = simpler management, lower transaction costs
- Still plenty of diversification for tax loss harvesting between baskets

## The 3 Baskets (Balanced for ~33% Each)

| Basket | Tickers | Portfolio Weight | Characteristics |
|--------|---------|------------------|----------------|
| **Basket 1** | 3 | 32.82% | Mega-Caps + SpaceX - SPACEX, NVDA, AAPL |
| **Basket 2** | 7 | 38.43% | Large Caps - MSFT, AMZN, GOOGL, GOOG, AVGO, META, TSLA |
| **Basket 3** | 40 | 28.75% | Broad exposure - MU, WMT, AMD, ASML, INTC, CSCO, COST... |

Each basket is **market-cap weighted internally**, just like QQQ itself.

### SpaceX Placeholder (SPACEX)
- **Weight**: 8.52% of portfolio (~26% of Basket 1)
- **Purpose**: Reserve allocation for when SpaceX IPOs
- **Current holding**: Buy QQQ or keep as cash until IPO
- **When SpaceX IPOs**: Replace placeholder with actual SPCX shares

## Strategy Mechanics

### Weekly Contribution ($500)
1. Check current value of all 3 baskets
2. Add $500 to the **most underweight basket** (lowest current value)
3. This naturally rebalances toward equal dollar exposure

### Tax Loss Harvesting (when a basket drops >10%)
1. **Sell** the losing basket (realize the loss for tax purposes)
2. **Buy** a different basket (maintains QQQ exposure)
3. **Wait 30 days** before rebuying the original basket (wash sale rule)
4. Use harvested losses to offset capital gains or up to $3,000 of ordinary income

### Charitable Donations (when shares appreciate >20%)
1. **Donate appreciated shares directly** to charity (in-kind transfer)
2. **Avoid capital gains tax** on the appreciation
3. **Get tax deduction** for the full market value
4. Replace donated shares by buying the same basket with new contributions

## Tax Benefits

| Strategy | Tax Benefit | Estimated Annual Value* |
|----------|-------------|------------------------|
| Tax Loss Harvesting | Loss deduction at marginal rate | ~$1,000-3,000 |
| Charitable Donations | Avoid gains + deduction | ~$500-2,000 |
| Rebalancing | Maintains target allocation | Risk reduction |

*Based on $500/week ($26,000/year) contributions, varies with market conditions

## Files

| File | Description |
|------|-------------|
| `create_three_baskets_with_spacex.py` | Creates the 3 baskets from top 50 Nasdaq 100 stocks + SpaceX placeholder |
| `basket_rotation_strategy.py` | Backtests the full tax loss harvesting strategy |
| `generate_basket_pdf.py` | Generates PDF report with basket details and pie chart |
| `fidelity_baskets_report.pdf` | Visual PDF report of all baskets |
| `baskets/basket_1_with_spacex.csv` | Basket 1 tickers and weights |
| `baskets/basket_2_with_spacex.csv` | Basket 2 tickers and weights |
| `baskets/basket_3_with_spacex.csv` | Basket 3 tickers and weights |
| `baskets/all_baskets_with_spacex.csv` | Combined view of all baskets |

## Running the Strategy

### 1. Create Baskets
```bash
python3 create_three_baskets_with_spacex.py
```

### 2. Generate PDF Report
```bash
python3 generate_basket_pdf.py
```

### 3. Run Backtest
```bash
python3 basket_rotation_strategy.py
```

## Example Basket 1 (Mega-Caps + SpaceX)

| Ticker | Portfolio Weight | Basket Internal Weight |
|--------|-----------------|----------------------|
| SPACEX | 8.52% | 25.96% |
| NVDA | 12.73% | 38.79% |
| AAPL | 11.57% | 35.25% |

**Basket 1 Total: 32.82% of portfolio**

## Example Basket 2 (Large Caps)

| Ticker | Portfolio Weight | Basket Internal Weight |
|--------|-----------------|----------------------|
| MSFT | 7.94% | 20.66% |
| AMZN | 6.78% | 17.64% |
| GOOGL | 5.91% | 15.38% |
| GOOG | 5.50% | 14.31% |
| AVGO | 4.68% | 12.18% |
| META | 3.86% | 10.04% |
| TSLA | 3.76% | 9.79% |

**Basket 2 Total: 38.43% of portfolio**

## Key Advantages

1. **Maintains QQQ Exposure** - Top 50 = ~93% of index
2. **Tax Efficient** - Harvest losses without changing market exposure
3. **Simple** - Only 3 baskets to manage
4. **Flexible** - Easy to adjust contribution amounts
5. **Charitable** - Built-in donation optimization
6. **SpaceX Ready** - Pre-allocated placeholder for SpaceX IPO

## Risks & Considerations

- **Tracking Error** - Top 50 may deviate slightly from full QQQ
- **Transaction Costs** - Frequent swapping incurs fees
- **Wash Sale Rule** - 30-day waiting period between swaps
- **Tax Complexity** - Requires careful record keeping
- **Market Risk** - Still fully exposed to Nasdaq 100 volatility
- **SpaceX Uncertainty** - IPO timing and valuation unknown

## Requirements

- Python 3.8+
- yfinance
- pandas
- numpy
- matplotlib

## Disclaimer

This is for educational and research purposes only. Consult a tax professional before implementing any tax loss harvesting strategy. Past performance does not guarantee future results.
