"""
Generate a PDF report of the 3 Fidelity Tax Loss Harvesting Baskets
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os

# Read basket CSV files
basket1 = pd.read_csv('baskets/basket_1_with_spacex.csv')
basket2 = pd.read_csv('baskets/basket_2_with_spacex.csv')
basket3 = pd.read_csv('baskets/basket_3_with_spacex.csv')

# Create PDF
pdf_path = 'fidelity_baskets_report.pdf'

with PdfPages(pdf_path) as pdf:
    # Page 1: Title and Overview
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis('off')
    
    title_text = """
    FIDELITY TAX LOSS HARVESTING STRATEGY
    ======================================
    
    3 Baskets of Nasdaq 100 Stocks (Top 50)
    
    Strategy Overview:
    • Each week: Add $500 to basket with lowest current value
    • Tax Loss Harvest: Sell basket if down >10%, buy different basket
    • Charitable Donations: Donate shares up >20% to avoid capital gains
    • Wash Sale Rule: Wait 30 days before rebuying same basket
    
    Basket Composition:
    • Basket 1: Mega-Caps (NVDA, AAPL, MSFT, AMZN) + SPACEX
    • Basket 2: Large-Caps (GOOGL, GOOG, AVGO, META, TSLA, etc.)
    • Basket 3: Mid-Caps (AMD, ASML, INTC, CSCO, COST, etc.)
    
    Total: 50 tickers (49 real + 1 SPACEX placeholder)
    """
    
    ax.text(0.5, 0.5, title_text, transform=ax.transAxes, fontsize=14,
            verticalalignment='center', horizontalalignment='center',
            family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()
    
    # Page 2: Basket 1
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis('off')
    
    # Calculate actual portfolio weights from basket_weight column
    b1_portfolio = basket1['basket_weight'].sum()
    b2_portfolio = basket2['basket_weight'].sum()
    b3_portfolio = basket3['basket_weight'].sum()
    
    basket1_text = f"BASKET 1 - Mega-Caps + SpaceX ({b1_portfolio:.2f}% of portfolio)\n"
    basket1_text += "=" * 60 + "\n\n"
    for _, row in basket1.iterrows():
        basket1_text += f"{row['ticker']:<10} {row['basket_pct']:>8.2f}%\n"
    basket1_text += "\n" + "=" * 60 + "\n"
    basket1_text += f"Total: {len(basket1)} tickers, 100.00%\n"
    
    ax.text(0.1, 0.95, basket1_text, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()
    
    # Page 3: Basket 2
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis('off')
    
    basket2_text = f"BASKET 2 - Large-Caps ({b2_portfolio:.2f}% of portfolio)\n"
    basket2_text += "=" * 60 + "\n\n"
    for _, row in basket2.iterrows():
        basket2_text += f"{row['ticker']:<10} {row['basket_pct']:>8.2f}%\n"
    basket2_text += "\n" + "=" * 60 + "\n"
    basket2_text += f"Total: {len(basket2)} tickers, 100.00%\n"
    
    ax.text(0.1, 0.95, basket2_text, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()
    
    # Page 4: Basket 3
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis('off')
    
    basket3_text = f"BASKET 3 - Mid-Caps ({b3_portfolio:.2f}% of portfolio)\n"
    basket3_text += "=" * 60 + "\n\n"
    for _, row in basket3.iterrows():
        basket3_text += f"{row['ticker']:<10} {row['basket_pct']:>8.2f}%\n"
    basket3_text += "\n" + "=" * 60 + "\n"
    basket3_text += f"Total: {len(basket3)} tickers, 100.00%\n"
    
    ax.text(0.1, 0.95, basket3_text, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.3))
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()
    
    # Page 5: Pie Chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
    
    # Portfolio allocation pie chart (dynamic from CSV data)
    labels = ['Basket 1\n(Mega-Caps)', 'Basket 2\n(Large-Caps)', 'Basket 3\n(Mid-Caps)']
    sizes = [b1_portfolio, b2_portfolio, b3_portfolio]
    colors = ['lightblue', 'lightgreen', 'lightyellow']
    explode = (0.05, 0.05, 0.05)
    
    ax1.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=90)
    ax1.set_title('Portfolio Allocation by Basket', fontsize=14, fontweight='bold')
    
    # Basket 1 breakdown
    ax2.axis('off')
    breakdown_text = "BASKET 1 BREAKDOWN\n" + "=" * 40 + "\n\n"
    for _, row in basket1.iterrows():
        breakdown_text += f"{row['ticker']:<10} {row['basket_pct']:>8.2f}%\n"
    
    ax2.text(0.1, 0.9, breakdown_text, transform=ax2.transAxes, fontsize=11,
             verticalalignment='top', family='monospace')
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

print(f"✅ PDF generated: {os.path.abspath(pdf_path)}")
print(f"   Pages: 5 (Overview, Basket 1, Basket 2, Basket 3, Visual Summary)")
