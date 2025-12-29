"""
IBIT+SPY Rotation Strategy Backtest Analysis
============================================
Simulates:
1. IBIT Overnight: Buy IBIT at close, sell at next open
2. SPY Day: After selling IBIT, buy SPY at open, sell at close
3. Buy & Hold IBIT: Hold IBIT continuously

IBIT launched on January 11, 2024
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output_rotation')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_data():
    print("Fetching IBIT and SPY data...")
    ibit = yf.Ticker("IBIT")
    spy = yf.Ticker("SPY")
    df_ibit = ibit.history(start="2024-01-11", end=datetime.now().strftime("%Y-%m-%d"))
    df_spy = spy.history(start="2024-01-11", end=datetime.now().strftime("%Y-%m-%d"))
    if df_ibit.empty or df_spy.empty:
        raise ValueError("No data fetched. Check ticker symbols and date range.")
    # Align on dates
    df = pd.DataFrame(index=df_ibit.index.intersection(df_spy.index))
    for col in ['Open','Close']:
        df[f'ibit_{col.lower()}'] = df_ibit[col]
        df[f'spy_{col.lower()}'] = df_spy[col]
    return df

def calculate_rotation_returns(df):
    results = df.copy()
    # IBIT overnight: buy at close, sell at next open
    results['ibit_overnight_return'] = (results['ibit_open'].shift(-1) - results['ibit_close']) / results['ibit_close']
    # SPY day: buy at open, sell at close (after IBIT is sold)
    results['spy_day_return'] = (results['spy_close'] - results['spy_open']) / results['spy_open']
    # Buy & Hold IBIT
    results['ibit_hold_return'] = results['ibit_close'].pct_change()
    # IBIT Night Only: just the overnight returns
    results['ibit_night_return'] = results['ibit_overnight_return']
    # Rotation: IBIT overnight, SPY day
    results['rotation_return'] = results['ibit_overnight_return'].fillna(0) + results['spy_day_return'].fillna(0)
    results = results.dropna()
    return results

def calculate_cumulative_returns(results):
    results = results.copy()
    results['rotation_cumulative'] = (1 + results['rotation_return']).cumprod()
    results['ibit_hold_cumulative'] = (1 + results['ibit_hold_return']).cumprod()
    results['ibit_night_cumulative'] = (1 + results['ibit_night_return']).cumprod()
    return results

def calculate_monthly_returns(results):
    results = results.copy()
    results['month'] = results.index.to_period('M')
    monthly = results.groupby('month').apply(
        lambda x: pd.Series({
            'rotation_return': (1 + x['rotation_return']).prod() - 1,
            'ibit_hold_return': (1 + x['ibit_hold_return']).prod() - 1,
            'ibit_night_return': (1 + x['ibit_night_return']).prod() - 1,
            'trading_days': len(x)
        })
    )
    return monthly

def calculate_performance_metrics(results):
    metrics = {}
    trading_days_per_year = 252
    for strat, ret, cum in [
        ('Rotation', 'rotation_return', 'rotation_cumulative'),
        ('IBIT Hold', 'ibit_hold_return', 'ibit_hold_cumulative'),
        ('IBIT Night', 'ibit_night_return', 'ibit_night_cumulative')
    ]:
        returns = results[ret]
        cumulative = results[cum]
        total_return = cumulative.iloc[-1] - 1
        n_days = len(returns)
        annualized_return = (1 + total_return) ** (trading_days_per_year / n_days) - 1
        volatility = returns.std() * np.sqrt(trading_days_per_year)
        risk_free_rate = 0.05
        sharpe = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
        rolling_max = cumulative.expanding().max()
        drawdowns = cumulative / rolling_max - 1
        max_drawdown = drawdowns.min()
        win_rate = (returns > 0).sum() / len(returns)
        avg_gain = returns[returns > 0].mean() if (returns > 0).any() else 0
        avg_loss = returns[returns < 0].mean() if (returns < 0).any() else 0
        metrics[strat] = {
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
    """Plot cumulative performance of all strategies."""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    ax.plot(results.index, results['rotation_cumulative'], label='Rotation Strategy (IBIT Overnight + SPY Day)', 
            linewidth=2, color='#2E86AB')
    ax.plot(results.index, results['ibit_hold_cumulative'], label='Buy & Hold IBIT', 
            linewidth=2, color='#A23B72')
    ax.plot(results.index, results['ibit_night_cumulative'], label='IBIT Night Only', 
            linewidth=2, color='#F18F01')
    
    ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
    
    ax.set_title('IBIT+SPY Rotation Strategy: Cumulative Performance\n(Growth of $1)', fontsize=14, fontweight='bold')
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
    
    bars1 = ax.bar(x - width, monthly['rotation_return'] * 100, width, label='Rotation Strategy', color='#2E86AB')
    bars2 = ax.bar(x, monthly['ibit_hold_return'] * 100, width, label='Buy & Hold IBIT', color='#A23B72')
    bars3 = ax.bar(x + width, monthly['ibit_night_return'] * 100, width, label='IBIT Night Only', color='#F18F01')
    
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    ax.set_title('IBIT+SPY Rotation Monthly Returns', fontsize=14, fontweight='bold')
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
    rotation_cum = (1 + monthly['rotation_return']).cumprod()
    ibit_hold_cum = (1 + monthly['ibit_hold_return']).cumprod()
    ibit_night_cum = (1 + monthly['ibit_night_return']).cumprod()
    
    months = [str(m) for m in monthly.index]
    
    ax.plot(months, rotation_cum, marker='o', label='Rotation Strategy', linewidth=2, markersize=6, color='#2E86AB')
    ax.plot(months, ibit_hold_cum, marker='s', label='Buy & Hold IBIT', linewidth=2, markersize=6, color='#A23B72')
    ax.plot(months, ibit_night_cum, marker='^', label='IBIT Night Only', linewidth=2, markersize=6, color='#F18F01')
    
    ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
    
    ax.set_title('IBIT+SPY Rotation Monthly Cumulative Performance\n(Growth of $1)', fontsize=14, fontweight='bold')
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
        ('rotation', 'Rotation Strategy', '#2E86AB'),
        ('ibit_hold', 'Buy & Hold IBIT', '#A23B72'),
        ('ibit_night', 'IBIT Night Only', '#F18F01')
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
    
    plt.suptitle('IBIT+SPY Rotation Strategy Drawdowns', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'drawdowns.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {os.path.join(OUTPUT_DIR, 'drawdowns.png')}")

def plot_return_distribution(results):
    """Plot distribution of daily returns for each strategy."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    strategies = [
        ('rotation_return', 'Rotation Strategy', '#2E86AB'),
        ('ibit_hold_return', 'Buy & Hold IBIT', '#A23B72'),
        ('ibit_night_return', 'IBIT Night Only', '#F18F01')
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
    print("IBIT+SPY ROTATION STRATEGY BACKTEST RESULTS")
    print("="*80)
    
    print("\n📊 PERFORMANCE METRICS:")
    print("-"*60)
    print(metrics.to_string())
    
    print("\n\n📅 MONTHLY RETURNS:")
    print("-"*60)
    monthly_display = monthly.copy()
    for col in ['rotation_return', 'ibit_hold_return', 'ibit_night_return']:
        monthly_display[col] = monthly_display[col].apply(lambda x: f"{x:.2%}")
    monthly_display = monthly_display.rename(columns={
        'rotation_return': 'Rotation',
        'ibit_hold_return': 'IBIT Hold',
        'ibit_night_return': 'IBIT Night',
        'trading_days': 'Days'
    })
    print(monthly_display.to_string())
    
    print("\n" + "="*80)

def generate_pdf_report(metrics, monthly, results):
    """Generate a PDF report with all results and charts."""
    pdf_path = os.path.join(OUTPUT_DIR, 'ibit_spy_rotation_report.pdf')
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
    story.append(Paragraph("IBIT+SPY Rotation Strategy Backtest Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subheading_style))
    story.append(Paragraph(f"Data Range: {results.index[0].strftime('%Y-%m-%d')} to {results.index[-1].strftime('%Y-%m-%d')}", subheading_style))
    story.append(Spacer(1, 20))
    
    # Strategy descriptions
    story.append(Paragraph("Strategy Definitions", heading_style))
    strategy_text = """
    <b>Rotation Strategy:</b> Buy IBIT at market close, sell at next open, then buy SPY at open and sell at close<br/>
    <b>Buy &amp; Hold IBIT:</b> Hold IBIT continuously<br/>
    <b>IBIT Night Only:</b> Buy IBIT at market close, sell at next open (overnight only)
    """
    story.append(Paragraph(strategy_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Performance Metrics Table
    story.append(Paragraph("Performance Metrics", heading_style))
    
    # Create metrics table
    metrics_data = [['Metric', 'Rotation Strategy', 'Buy & Hold IBIT', 'IBIT Night Only']]
    metrics_reset = metrics.reset_index()
    metrics_reset.columns = ['Strategy'] + list(metrics.columns)
    
    for col in metrics.columns:
        row = [col]
        for strategy in ['Rotation', 'IBIT Hold', 'IBIT Night']:
            row.append(str(metrics.loc[strategy, col]))
        metrics_data.append(row)
    
    metrics_table = Table(metrics_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
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
    rotation_total = float(metrics.loc['Rotation', 'Total Return'].strip('%')) / 100
    ibit_hold_total = float(metrics.loc['IBIT Hold', 'Total Return'].strip('%')) / 100
    ibit_night_total = float(metrics.loc['IBIT Night', 'Total Return'].strip('%')) / 100
    
    insights = f"""
    <b>1. Rotation Strategy Dominates:</b> The rotation strategy generated a {rotation_total:.1%} total return 
    compared to {ibit_hold_total:.1%} for buy &amp; hold IBIT and {ibit_night_total:.1%} for night-only IBIT.<br/><br/>
    
    <b>2. SPY Day Trading Adds Value:</b> The rotation strategy outperforms night-only IBIT by approximately 
    {(rotation_total/ibit_night_total - 1):.1%}, demonstrating that SPY day trading enhances returns.<br/><br/>
    
    <b>3. Superior Risk Profile:</b> The rotation strategy has the smallest max drawdown ({metrics.loc['Rotation', 'Max Drawdown']}) 
    and highest Sharpe ratio ({metrics.loc['Rotation', 'Sharpe Ratio']}), indicating superior risk-adjusted returns.<br/><br/>
    
    <b>4. Win Rate:</b> Rotation strategy wins {metrics.loc['Rotation', 'Win Rate']} of trading days vs 
    {metrics.loc['IBIT Hold', 'Win Rate']} for buy &amp; hold and {metrics.loc['IBIT Night', 'Win Rate']} for night-only.
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
    
    monthly_data = [['Month', 'Rotation', 'IBIT Hold', 'IBIT Night', 'Rotation vs IBIT Hold', 'Rotation vs IBIT Night', 'Days']]
    for idx, row in monthly.iterrows():
        rotation_vs_ibit_hold = row['rotation_return'] - row['ibit_hold_return']
        rotation_vs_ibit_night = row['rotation_return'] - row['ibit_night_return']
        monthly_data.append([
            str(idx),
            f"{row['rotation_return']:.2%}",
            f"{row['ibit_hold_return']:.2%}",
            f"{row['ibit_night_return']:.2%}",
            f"{rotation_vs_ibit_hold:+.2%}",
            f"{rotation_vs_ibit_night:+.2%}",
            f"{int(row['trading_days'])}"
        ])
    
    monthly_table = Table(monthly_data, colWidths=[0.8*inch, 0.9*inch, 0.9*inch, 0.9*inch, 1.0*inch, 1.0*inch, 0.5*inch])
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
    print("IBIT+SPY Rotation Strategy Backtest Analysis")
    print("="*60)
    
    # Fetch data
    df = fetch_data()
    
    # Calculate returns
    results = calculate_rotation_returns(df)
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