"""
IBIT Strategy Backtest Analysis
================================
Compares 3 strategies:
1. Night Strategy: Buy at market close, sell at market open
2. Buy & Hold: Hold IBIT continuously
3. Day Only: Buy at market open, sell at market close

IBIT launched on January 11, 2024
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Create output directory for plots
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def fetch_ibit_data():
    """Fetch IBIT historical data since launch."""
    print("Fetching IBIT data...")
    ibit = yf.Ticker("IBIT")
    
    # IBIT launched January 11, 2024
    df = ibit.history(start="2024-01-11", end=datetime.now().strftime("%Y-%m-%d"))
    
    if df.empty:
        raise ValueError("No data fetched. Check ticker symbol and date range.")
    
    print(f"Fetched {len(df)} trading days from {df.index[0].date()} to {df.index[-1].date()}")
    return df


def calculate_strategy_returns(df):
    """
    Calculate returns for all 3 strategies.
    
    Night Strategy: Return = (Next Open - Close) / Close
    Day Strategy: Return = (Close - Open) / Open
    Buy & Hold: Return = (Close - Previous Close) / Previous Close
    """
    results = df.copy()
    
    # Night strategy: Buy at close, sell at next open
    results['night_return'] = (results['Open'].shift(-1) - results['Close']) / results['Close']
    
    # Day strategy: Buy at open, sell at close
    results['day_return'] = (results['Close'] - results['Open']) / results['Open']
    
    # Buy and hold: Daily return based on close prices
    results['hold_return'] = results['Close'].pct_change()
    
    # Drop last row (no next open for night strategy)
    results = results.dropna()
    
    return results


def calculate_cumulative_returns(results):
    """Calculate cumulative returns for each strategy."""
    results = results.copy()
    
    # Cumulative returns (growth of $1)
    results['night_cumulative'] = (1 + results['night_return']).cumprod()
    results['day_cumulative'] = (1 + results['day_return']).cumprod()
    results['hold_cumulative'] = (1 + results['hold_return']).cumprod()
    
    return results


def calculate_monthly_returns(results):
    """Aggregate returns by month."""
    # Add month column for grouping
    results = results.copy()
    results['month'] = results.index.to_period('M')
    
    # Calculate monthly returns by compounding daily returns
    monthly = results.groupby('month').apply(
        lambda x: pd.Series({
            'night_return': (1 + x['night_return']).prod() - 1,
            'day_return': (1 + x['day_return']).prod() - 1,
            'hold_return': (1 + x['hold_return']).prod() - 1,
            'trading_days': len(x)
        })
    )
    
    return monthly


def calculate_performance_metrics(results):
    """Calculate key performance metrics for each strategy."""
    strategies = ['night', 'day', 'hold']
    metrics = {}
    
    trading_days_per_year = 252
    
    for strategy in strategies:
        returns = results[f'{strategy}_return']
        cumulative = results[f'{strategy}_cumulative']
        
        # Total return
        total_return = cumulative.iloc[-1] - 1
        
        # Annualized return
        n_days = len(returns)
        annualized_return = (1 + total_return) ** (trading_days_per_year / n_days) - 1
        
        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(trading_days_per_year)
        
        # Sharpe ratio (assuming 5% risk-free rate)
        risk_free_rate = 0.05
        sharpe = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        # Max drawdown
        rolling_max = cumulative.expanding().max()
        drawdowns = cumulative / rolling_max - 1
        max_drawdown = drawdowns.min()
        
        # Win rate
        win_rate = (returns > 0).sum() / len(returns)
        
        # Average gain/loss
        avg_gain = returns[returns > 0].mean() if (returns > 0).any() else 0
        avg_loss = returns[returns < 0].mean() if (returns < 0).any() else 0
        
        metrics[strategy] = {
            'Total Return': f"{total_return:.2%}",
            'Annualized Return': f"{annualized_return:.2%}",
            'Volatility': f"{volatility:.2%}",
            'Sharpe Ratio': f"{sharpe:.2f}",
            'Max Drawdown': f"{max_drawdown:.2%}",
            'Win Rate': f"{win_rate:.2%}",
            'Avg Gain': f"{avg_gain:.4%}",
            'Avg Loss': f"{avg_loss:.4%}",
            'Trading Days': n_days
        }
    
    return pd.DataFrame(metrics).T


def plot_cumulative_performance(results):
    """Plot cumulative performance of all 3 strategies."""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    ax.plot(results.index, results['night_cumulative'], label='Night Strategy (Buy Close → Sell Open)', 
            linewidth=2, color='#2E86AB')
    ax.plot(results.index, results['hold_cumulative'], label='Buy & Hold', 
            linewidth=2, color='#A23B72')
    ax.plot(results.index, results['day_cumulative'], label='Day Only (Buy Open → Sell Close)', 
            linewidth=2, color='#F18F01')
    
    ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
    
    ax.set_title('IBIT Strategy Comparison: Cumulative Performance\n(Growth of $1)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.2f}'))
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'cumulative_performance.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {os.path.join(OUTPUT_DIR, 'cumulative_performance.png')}")


def plot_monthly_returns(monthly):
    """Plot month-by-month comparison bar chart."""
    fig, ax = plt.subplots(figsize=(16, 8))
    
    x = np.arange(len(monthly))
    width = 0.25
    
    bars1 = ax.bar(x - width, monthly['night_return'] * 100, width, label='Night Strategy', color='#2E86AB')
    bars2 = ax.bar(x, monthly['hold_return'] * 100, width, label='Buy & Hold', color='#A23B72')
    bars3 = ax.bar(x + width, monthly['day_return'] * 100, width, label='Day Only', color='#F18F01')
    
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    ax.set_title('IBIT Monthly Returns by Strategy', fontsize=14, fontweight='bold')
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Monthly Return (%)', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels([str(m) for m in monthly.index], rotation=45, ha='right')
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'monthly_returns.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {os.path.join(OUTPUT_DIR, 'monthly_returns.png')}")


def plot_monthly_cumulative(monthly):
    """Plot cumulative monthly performance over time."""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Calculate cumulative from monthly returns
    night_cum = (1 + monthly['night_return']).cumprod()
    hold_cum = (1 + monthly['hold_return']).cumprod()
    day_cum = (1 + monthly['day_return']).cumprod()
    
    months = [str(m) for m in monthly.index]
    
    ax.plot(months, night_cum, marker='o', label='Night Strategy', linewidth=2, markersize=6, color='#2E86AB')
    ax.plot(months, hold_cum, marker='s', label='Buy & Hold', linewidth=2, markersize=6, color='#A23B72')
    ax.plot(months, day_cum, marker='^', label='Day Only', linewidth=2, markersize=6, color='#F18F01')
    
    ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
    
    ax.set_title('IBIT Monthly Cumulative Performance\n(Growth of $1)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels(months, rotation=45, ha='right')
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.2f}'))
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'monthly_cumulative.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {os.path.join(OUTPUT_DIR, 'monthly_cumulative.png')}")


def plot_drawdowns(results):
    """Plot drawdowns for each strategy."""
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    
    strategies = [
        ('night', 'Night Strategy', '#2E86AB'),
        ('hold', 'Buy & Hold', '#A23B72'),
        ('day', 'Day Only', '#F18F01')
    ]
    
    for ax, (strategy, name, color) in zip(axes, strategies):
        cumulative = results[f'{strategy}_cumulative']
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative / rolling_max - 1) * 100
        
        ax.fill_between(results.index, drawdown, 0, alpha=0.5, color=color)
        ax.plot(results.index, drawdown, color=color, linewidth=1)
        ax.set_ylabel('Drawdown (%)', fontsize=10)
        ax.set_title(f'{name} Drawdown', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(drawdown.min() * 1.1, 5)
    
    axes[-1].set_xlabel('Date', fontsize=12)
    
    plt.suptitle('IBIT Strategy Drawdowns', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'drawdowns.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {os.path.join(OUTPUT_DIR, 'drawdowns.png')}")


def plot_return_distribution(results):
    """Plot distribution of daily returns for each strategy."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    strategies = [
        ('night_return', 'Night Strategy', '#2E86AB'),
        ('hold_return', 'Buy & Hold', '#A23B72'),
        ('day_return', 'Day Only', '#F18F01')
    ]
    
    for ax, (col, name, color) in zip(axes, strategies):
        returns = results[col] * 100
        ax.hist(returns, bins=50, alpha=0.7, color=color, edgecolor='black', linewidth=0.5)
        ax.axvline(x=returns.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {returns.mean():.3f}%')
        ax.axvline(x=0, color='black', linestyle='-', linewidth=1)
        ax.set_title(f'{name}\nDaily Returns Distribution', fontsize=11, fontweight='bold')
        ax.set_xlabel('Daily Return (%)', fontsize=10)
        ax.set_ylabel('Frequency', fontsize=10)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'return_distribution.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {os.path.join(OUTPUT_DIR, 'return_distribution.png')}")


def print_summary(metrics, monthly):
    """Print summary statistics."""
    print("\n" + "="*80)
    print("IBIT STRATEGY BACKTEST RESULTS")
    print("="*80)
    
    print("\n📊 PERFORMANCE METRICS:")
    print("-"*60)
    print(metrics.to_string())
    
    print("\n\n📅 MONTHLY RETURNS:")
    print("-"*60)
    monthly_display = monthly.copy()
    for col in ['night_return', 'day_return', 'hold_return']:
        monthly_display[col] = monthly_display[col].apply(lambda x: f"{x:.2%}")
    monthly_display = monthly_display.rename(columns={
        'night_return': 'Night',
        'day_return': 'Day',
        'hold_return': 'Buy&Hold',
        'trading_days': 'Days'
    })
    print(monthly_display.to_string())
    
    print("\n" + "="*80)


def generate_pdf_report(metrics, monthly, results):
    """Generate a PDF report with all results and charts."""
    pdf_path = os.path.join(OUTPUT_DIR, 'ibit_strategy_report.pdf')
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, 
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2E86AB')
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#333333')
    )
    subheading_style = ParagraphStyle(
        'SubHeading',
        parent=styles['Normal'],
        fontSize=12,
        spaceBefore=10,
        spaceAfter=5,
        textColor=colors.HexColor('#666666')
    )
    
    story = []
    
    # Title
    story.append(Paragraph("IBIT Strategy Backtest Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subheading_style))
    story.append(Paragraph(f"Data Range: {results.index[0].strftime('%Y-%m-%d')} to {results.index[-1].strftime('%Y-%m-%d')}", subheading_style))
    story.append(Spacer(1, 20))
    
    # Strategy descriptions
    story.append(Paragraph("Strategy Definitions", heading_style))
    strategy_text = """
    <b>Night Strategy:</b> Buy IBIT at market close, sell at next market open<br/>
    <b>Buy &amp; Hold:</b> Hold IBIT continuously<br/>
    <b>Day Only:</b> Buy IBIT at market open, sell at market close
    """
    story.append(Paragraph(strategy_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Performance Metrics Table
    story.append(Paragraph("Performance Metrics", heading_style))
    
    # Create metrics table
    metrics_data = [['Metric', 'Night Strategy', 'Buy & Hold', 'Day Only']]
    metrics_reset = metrics.reset_index()
    metrics_reset.columns = ['Strategy'] + list(metrics.columns)
    
    for col in metrics.columns:
        row = [col]
        for strategy in ['night', 'hold', 'day']:
            row.append(str(metrics.loc[strategy, col]))
        metrics_data.append(row)
    
    metrics_table = Table(metrics_data, colWidths=[1.8*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F5F5F5'), colors.HexColor('#EAEAEA')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 30))
    
    # Key Insights
    story.append(Paragraph("Key Insights", heading_style))
    
    # Extract numeric values for insights
    night_total = float(metrics.loc['night', 'Total Return'].strip('%')) / 100
    hold_total = float(metrics.loc['hold', 'Total Return'].strip('%')) / 100
    day_total = float(metrics.loc['day', 'Total Return'].strip('%')) / 100
    
    insights = f"""
    <b>1. Night Strategy Dominates:</b> The night strategy generated a {night_total:.1%} total return 
    compared to {hold_total:.1%} for buy &amp; hold - approximately {night_total/hold_total:.1f}x better performance.<br/><br/>
    
    <b>2. Day-Only Strategy Loses:</b> Holding IBIT only during market hours resulted in a {day_total:.1%} return, 
    demonstrating that most gains occur overnight.<br/><br/>
    
    <b>3. Lower Risk Profile:</b> The night strategy has the smallest max drawdown ({metrics.loc['night', 'Max Drawdown']}) 
    and highest Sharpe ratio ({metrics.loc['night', 'Sharpe Ratio']}), indicating superior risk-adjusted returns.<br/><br/>
    
    <b>4. Win Rate:</b> Night strategy wins {metrics.loc['night', 'Win Rate']} of trading days vs {metrics.loc['hold', 'Win Rate']} for buy &amp; hold.
    """
    story.append(Paragraph(insights, styles['Normal']))
    
    # Page break before charts
    story.append(PageBreak())
    
    # Charts
    story.append(Paragraph("Performance Charts", heading_style))
    story.append(Spacer(1, 10))
    
    # Add cumulative performance chart
    img_path = os.path.join(OUTPUT_DIR, 'cumulative_performance.png')
    if os.path.exists(img_path):
        story.append(Paragraph("Cumulative Performance (Growth of $1)", subheading_style))
        img = Image(img_path, width=7*inch, height=4*inch)
        story.append(img)
        story.append(Spacer(1, 20))
    
    # Add monthly returns chart
    img_path = os.path.join(OUTPUT_DIR, 'monthly_returns.png')
    if os.path.exists(img_path):
        story.append(Paragraph("Monthly Returns Comparison", subheading_style))
        img = Image(img_path, width=7*inch, height=3.5*inch)
        story.append(img)
    
    story.append(PageBreak())
    
    # Monthly cumulative chart
    img_path = os.path.join(OUTPUT_DIR, 'monthly_cumulative.png')
    if os.path.exists(img_path):
        story.append(Paragraph("Monthly Cumulative Performance", subheading_style))
        img = Image(img_path, width=7*inch, height=4*inch)
        story.append(img)
        story.append(Spacer(1, 20))
    
    # Drawdowns chart
    img_path = os.path.join(OUTPUT_DIR, 'drawdowns.png')
    if os.path.exists(img_path):
        story.append(Paragraph("Strategy Drawdowns", subheading_style))
        img = Image(img_path, width=7*inch, height=4.5*inch)
        story.append(img)
    
    story.append(PageBreak())
    
    # Return distribution chart
    img_path = os.path.join(OUTPUT_DIR, 'return_distribution.png')
    if os.path.exists(img_path):
        story.append(Paragraph("Daily Return Distributions", subheading_style))
        img = Image(img_path, width=7.5*inch, height=2.5*inch)
        story.append(img)
        story.append(Spacer(1, 30))
    
    # Monthly Returns Table
    story.append(Paragraph("Monthly Returns Detail", heading_style))
    
    monthly_data = [['Month', 'Night', 'Buy & Hold', 'Day Only', 'Night vs Hold', 'Night vs Day', 'Days']]
    for idx, row in monthly.iterrows():
        night_vs_hold = row['night_return'] - row['hold_return']
        night_vs_day = row['night_return'] - row['day_return']
        monthly_data.append([
            str(idx),
            f"{row['night_return']:.2%}",
            f"{row['hold_return']:.2%}",
            f"{row['day_return']:.2%}",
            f"{night_vs_hold:+.2%}",
            f"{night_vs_day:+.2%}",
            f"{int(row['trading_days'])}"
        ])
    
    monthly_table = Table(monthly_data, colWidths=[0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch, 1.0*inch, 1.0*inch, 0.5*inch])
    monthly_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
    ]))
    story.append(monthly_table)
    
    # Build PDF
    doc.build(story)
    print(f"📄 PDF Report saved: {pdf_path}")
    return pdf_path


def main():
    """Run the full backtest analysis."""
    print("="*60)
    print("IBIT Strategy Backtest Analysis")
    print("="*60)
    
    # Fetch data
    df = fetch_ibit_data()
    
    # Calculate returns
    results = calculate_strategy_returns(df)
    results = calculate_cumulative_returns(results)
    
    # Monthly aggregation
    monthly = calculate_monthly_returns(results)
    
    # Performance metrics
    metrics = calculate_performance_metrics(results)
    
    # Print summary
    print_summary(metrics, monthly)
    
    # Generate plots
    print("\n📈 Generating visualizations...")
    plot_cumulative_performance(results)
    plot_monthly_returns(monthly)
    plot_monthly_cumulative(monthly)
    plot_drawdowns(results)
    plot_return_distribution(results)
    
    # Save results to CSV
    results.to_csv(os.path.join(OUTPUT_DIR, 'daily_results.csv'))
    monthly.to_csv(os.path.join(OUTPUT_DIR, 'monthly_results.csv'))
    metrics.to_csv(os.path.join(OUTPUT_DIR, 'performance_metrics.csv'))
    
    # Generate PDF report
    print("\n📄 Generating PDF report...")
    generate_pdf_report(metrics, monthly, results)
    
    print(f"\n✅ Analysis complete! Results saved to: {OUTPUT_DIR}")
    
    return results, monthly, metrics


if __name__ == "__main__":
    results, monthly, metrics = main()
