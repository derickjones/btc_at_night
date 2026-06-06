"""
Create 3 Baskets from Top 50 Nasdaq 100 Stocks (with SpaceX placeholder)
=======================================================================
Same as the original 3-basket strategy, but with a QQQ placeholder for SpaceX.

When SpaceX IPOs:
1. Sell the QQQ placeholder
2. Buy SpaceX at ~8.6% weight
3. SpaceX goes to Basket 1

Until then, the QQQ placeholder gives you Nasdaq 100 exposure in that slot.
"""

import pandas as pd
import numpy as np
import os

# Nasdaq 100 components with weights (from provided data, June 2026)
NASDAQ100_COMPONENTS = {
    "NVDA": 12.90, "AAPL": 11.72, "MSFT": 8.04, "AMZN": 6.87,
    "GOOGL": 5.99, "GOOG": 5.57, "AVGO": 4.74, "META": 3.91,
    "TSLA": 3.81, "MU": 2.53, "WMT": 2.46, "AMD": 1.98,
    "ASML": 1.64, "INTC": 1.29, "CSCO": 1.25, "COST": 1.12,
    "LRCX": 0.99, "ARM": 0.95, "AMAT": 0.93, "NFLX": 0.90,
    "PLTR": 0.84, "TXN": 0.67, "KLAC": 0.65, "LIN": 0.61,
    "SNDK": 0.60, "MRVL": 0.60, "QCOM": 0.59, "PANW": 0.57,
    "ADI": 0.51, "PEP": 0.50, "TMUS": 0.50, "STX": 0.50,
    "AMGN": 0.49, "APP": 0.49, "WDC": 0.46, "CRWD": 0.44,
    "GILD": 0.42, "ISRG": 0.39, "SHOP": 0.37, "HON": 0.35,
    "BKNG": 0.33, "PDD": 0.31, "VRTX": 0.29, "SBUX": 0.28,
    "FTNT": 0.28, "CDNS": 0.27, "MAR": 0.27, "ADBE": 0.26,
    "ADP": 0.24, "CEG": 0.24, "SNPS": 0.23, "MNST": 0.23,
    "CSX": 0.23, "CMCSA": 0.22, "DDOG": 0.22, "MELI": 0.21,
    "INTU": 0.21, "MDLZ": 0.21, "ABNB": 0.21, "ORLY": 0.19,
    "NXPI": 0.19, "ROST": 0.19, "MPWR": 0.19, "CTAS": 0.19,
    "AEP": 0.18, "DASH": 0.18, "LITE": 0.17, "REGN": 0.17,
    "WBD": 0.17, "BKR": 0.16, "PCAR": 0.16, "FANG": 0.14,
    "FAST": 0.14, "EA": 0.13, "ODFL": 0.13, "XEL": 0.13,
    "ADSK": 0.13, "MCHP": 0.12, "FER": 0.12, "EXC": 0.12,
    "IDXX": 0.12, "MSTR": 0.11, "CCEP": 0.11, "KDP": 0.11,
    "ALNY": 0.11, "TTWO": 0.10, "AXON": 0.10, "TRI": 0.10,
    "PYPL": 0.09, "PAYX": 0.09, "WDAY": 0.09, "ROP": 0.09,
    "GEHC": 0.08, "CPRT": 0.07, "DXCM": 0.07, "KHC": 0.07,
    "CTSH": 0.07, "VRSK": 0.06, "ZS": 0.05, "INSM": 0.05,
    "CHTR": 0.04,
}

# SpaceX placeholder weight (estimated at IPO)
SPACEX_WEIGHT = 8.63  # Renormalized weight when added


def create_top50_baskets_with_spacex_placeholder(components, num_baskets=3):
    """
    Create baskets from top 50 Nasdaq 100 stocks with SpaceX placeholder.
    
    1. Take top 50 by index weight (~93% of QQQ)
    2. Replace CEG (smallest at 0.26%) with QQQ placeholder for SpaceX
    3. Renormalize to 100%
    4. Pack sequentially into 3 baskets
    
    Each basket maintains market-cap weighting internally.
    """
    # Take top 50
    sorted_all = sorted(components.items(), key=lambda x: x[1], reverse=True)
    top50 = sorted_all[:50]
    
    # Replace CEG with SpaceX placeholder
    # CEG is the last item in top50 (smallest weight)
    top50_no_ceg = [(t, w) for t, w in top50 if t != 'CEG']
    
    # Add SpaceX placeholder with estimated weight
    # Using SPACEX as placeholder until IPO
    top50_with_placeholder = top50_no_ceg + [('SPACEX', SPACEX_WEIGHT)]
    
    total_weight = sum(w for _, w in top50_with_placeholder)
    print(f"Top 50 covers {total_weight:.2f}% of QQQ index weight (with SpaceX placeholder)")
    
    # Renormalize to 100%
    renormalized = [(t, (w / total_weight) * 100) for t, w in top50_with_placeholder]
    
    # Pack into baskets with adjusted thresholds for ~33% each
    # Force SPACEX into Basket 1 by removing it first, then adding it back
    spacex_item = None
    others = []
    for ticker, weight in renormalized:
        if ticker == 'SPACEX':
            spacex_item = (ticker, weight)
        else:
            others.append((ticker, weight))
    
    # Force specific ticker counts: 3 in Basket 1, 7 in Basket 2, rest in Basket 3
    # This balances the heavy mega-caps across baskets
    baskets = {i: [] for i in range(1, num_baskets + 1)}
    
    # Add SPACEX to Basket 1 first
    if spacex_item:
        baskets[1].append(spacex_item)
    
    # Pack remaining stocks with forced counts
    for i, (ticker, weight) in enumerate(others):
        if len(baskets[1]) < 3:
            baskets[1].append((ticker, weight))
        elif len(baskets[2]) < 7:
            baskets[2].append((ticker, weight))
        else:
            baskets[3].append((ticker, weight))
    
    return baskets


def print_basket_summary(baskets):
    """Print summary of each basket."""
    print("=" * 80)
    print("NASDAQ 100 TOP 50 - 3 BASKETS (with SpaceX Placeholder)")
    print("=" * 80)
    print("Top 50 stocks cover ~93% of QQQ, renormalized to 100%")
    print("CEG removed, SPACEX placeholder added (~8.6% weight)")
    print()

    for basket_num, tickers in baskets.items():
        total_weight = sum(w for _, w in tickers)

        print(f"📦 BASKET {basket_num} ({len(tickers)} tickers, {total_weight:.2f}% of renormalized index)")
        print("-" * 80)
        print(f"{'#':<4} {'Ticker':<25} {'Basket Weight':<15}")
        print("-" * 80)

        for i, (ticker, weight) in enumerate(tickers):
            print(f"{i+1:<4} {ticker:<25} {weight:>10.2f}%")

        print("-" * 80)
        print(f"  Total: {len(tickers)} tickers, {total_weight:.2f}% weight")
        print()

    print("=" * 80)
    print("STRATEGY:")
    print("=" * 80)
    print("  1. Each week, add $500 to the basket with lowest current value")
    print("  2. This keeps all 3 baskets roughly equal in dollar terms")
    print("  3. If a basket drops >10% from cost basis, harvest the loss:")
    print("     - Sell the losing basket")
    print("     - Buy a different basket (maintains QQQ exposure)")
    print("  4. Donate appreciated shares (>+20%) to charity")
    print("     - Avoids capital gains tax")
    print("     - Gets tax deduction for full market value")
    print("  5. Wash sale rule: wait 30 days before rebuying same basket")
    print()
    print("  WHEN SPACEX IPOs:")
    print("     - SPACEX placeholder becomes actual SpaceX shares")
    print("     - Buy SpaceX (SPCX) at ~8.6% weight")
    print("     - SpaceX stays in Basket 1 (with NVDA, AAPL, MSFT)")
    print("=" * 80)


def save_baskets_to_files(baskets, output_dir):
    """Save basket tickers to CSV files."""
    os.makedirs(output_dir, exist_ok=True)

    for basket_num, tickers in baskets.items():
        total_weight = sum(w for _, w in tickers)
        df = pd.DataFrame([
            {
                'ticker': t, 
                'basket_weight': w,
                'basket_pct': (w / total_weight * 100) if total_weight > 0 else 0
            }
            for t, w in tickers
        ])
        filepath = os.path.join(output_dir, f'basket_{basket_num}_with_spacex.csv')
        df.to_csv(filepath, index=False)
        print(f"  Saved: {filepath}")

    # Save all baskets combined
    all_data = []
    for basket_num, tickers in baskets.items():
        for ticker, weight in tickers:
            all_data.append({
                'ticker': ticker,
                'basket': basket_num,
                'basket_weight': weight
            })

    df_all = pd.DataFrame(all_data)
    filepath = os.path.join(output_dir, 'all_baskets_with_spacex.csv')
    df_all.to_csv(filepath, index=False)
    print(f"  Saved: {filepath}")


def main():
    print("Creating 3 baskets from top 50 Nasdaq 100 stocks (with SpaceX placeholder)...\n")

    baskets = create_top50_baskets_with_spacex_placeholder(NASDAQ100_COMPONENTS, num_baskets=3)
    print_basket_summary(baskets)

    output_dir = os.path.join(os.path.dirname(__file__), 'baskets')
    print(f"\n💾 Saving basket files to: {output_dir}")
    save_baskets_to_files(baskets, output_dir)

    print("\n✅ Done! Basket files created with SpaceX placeholder.")
    return baskets


if __name__ == "__main__":
    baskets = main()
