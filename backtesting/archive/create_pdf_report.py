"""
PDF Report Generator for IBIT Overnight Trading Strategy Analysis
Creates a comprehensive PDF report with charts and analysis.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus.flowables import KeepTogether
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

def create_charts():
    """Create all charts for the PDF report."""
    
    print("📊 Creating charts for PDF report...")
    
    # Load data
    trade_results = pd.read_csv('results/trade_results.csv')
    performance = pd.read_csv('results/performance_summary.csv')
    
    # Parse dates
    trade_results['buy_date'] = pd.to_datetime(trade_results['buy_date'], utc=True)
    trade_results['sell_date'] = pd.to_datetime(trade_results['sell_date'], utc=True)
    
    # Ensure charts directory exists
    os.makedirs('results/pdf_charts', exist_ok=True)
    
    # Create rolling performance analysis charts first
    create_rolling_performance_charts(trade_results)
    
    # Continue with trade_results available for all chart creation
    
    # 1. Portfolio Performance Chart
    plt.figure(figsize=(12, 8))
    
    # Main portfolio chart
    plt.subplot(2, 1, 1)
    plt.plot(trade_results['sell_date'], trade_results['portfolio_value'], 'b-', linewidth=2, label='Portfolio Value')
    plt.axhline(y=10000, color='gray', linestyle='--', alpha=0.7, label='Initial Capital ($10,000)')
    plt.title('IBIT Overnight Strategy - Portfolio Performance Over Time', fontsize=14, fontweight='bold')
    plt.ylabel('Portfolio Value ($)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
def create_rolling_performance_charts(trade_results):
    """Create comprehensive rolling performance analysis charts."""
    
    print("📈 Creating rolling performance trend analysis...")
    
    # Prepare data
    df = trade_results.copy()
    df = df.sort_values('sell_date')
    
    # Calculate rolling metrics with different windows
    windows = [30, 60, 90, 120]  # Different rolling windows for analysis
    baseline_annual_return = 0.7232
    baseline_sharpe = 1.81
    baseline_win_rate = 0.5468
    
    # Create comprehensive rolling analysis
    fig = plt.figure(figsize=(20, 16))
    
    # Chart 1: Rolling Annual Returns vs Baseline
    ax1 = plt.subplot(3, 2, 1)
    
    for window in windows:
        if len(df) >= window:
            rolling_returns = df['net_return'].rolling(window=window).apply(
                lambda x: (1 + x).prod() ** (252/len(x)) - 1 if len(x) > 0 else np.nan
            )
            valid_data = rolling_returns.dropna()
            if len(valid_data) > 0:
                ax1.plot(df['sell_date'].iloc[window-1:], rolling_returns.iloc[window-1:], 
                        linewidth=2, alpha=0.8, label=f'{window}-trade window')
    
    ax1.axhline(y=baseline_annual_return, color='red', linestyle='--', linewidth=2, 
               alpha=0.7, label=f'Baseline ({baseline_annual_return:.1%})')
    ax1.axhline(y=0, color='black', linestyle=':', alpha=0.5)
    ax1.set_title('📈 Rolling Annual Returns - Strategy Edge Persistence', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Annual Return')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0%}'))
    
    # Chart 2: Rolling Win Rate vs Baseline
    ax2 = plt.subplot(3, 2, 2)
    
    for window in windows:
        if len(df) >= window:
            rolling_win_rate = (df['net_return'] > 0).rolling(window=window).mean()
            valid_data = rolling_win_rate.dropna()
            if len(valid_data) > 0:
                ax2.plot(df['sell_date'].iloc[window-1:], rolling_win_rate.iloc[window-1:], 
                        linewidth=2, alpha=0.8, label=f'{window}-trade window')
    
    ax2.axhline(y=baseline_win_rate, color='red', linestyle='--', linewidth=2, 
               alpha=0.7, label=f'Baseline ({baseline_win_rate:.1%})')
    ax2.axhline(y=0.5, color='black', linestyle=':', alpha=0.5, label='50% (Random)')
    ax2.set_title('🎯 Rolling Win Rate - Consistency Tracking', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Win Rate')
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax2.grid(True, alpha=0.3)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0%}'))
    
    # Chart 3: Rolling Sharpe Ratio vs Baseline
    ax3 = plt.subplot(3, 2, 3)
    
    for window in windows:
        if len(df) >= window:
            rolling_sharpe = (df['net_return'].rolling(window=window).mean() / 
                            df['net_return'].rolling(window=window).std()) * np.sqrt(252)
            valid_data = rolling_sharpe.dropna()
            if len(valid_data) > 0:
                ax3.plot(df['sell_date'].iloc[window-1:], rolling_sharpe.iloc[window-1:], 
                        linewidth=2, alpha=0.8, label=f'{window}-trade window')
    
    ax3.axhline(y=baseline_sharpe, color='red', linestyle='--', linewidth=2, 
               alpha=0.7, label=f'Baseline ({baseline_sharpe:.2f})')
    ax3.axhline(y=1.0, color='orange', linestyle=':', alpha=0.7, label='1.0 (Acceptable)')
    ax3.axhline(y=0, color='black', linestyle=':', alpha=0.5)
    ax3.set_title('📊 Rolling Sharpe Ratio - Risk-Adjusted Performance', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Sharpe Ratio')
    ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax3.grid(True, alpha=0.3)
    
    # Chart 4: Rolling Drawdown Analysis
    ax4 = plt.subplot(3, 2, 4)
    
    # Calculate rolling maximum drawdown
    for window in windows:
        if len(df) >= window:
            rolling_dd = []
            for i in range(window-1, len(df)):
                window_data = df.iloc[i-window+1:i+1]
                portfolio_values = window_data['portfolio_value'].values
                running_max = np.maximum.accumulate(portfolio_values)
                drawdown = (portfolio_values - running_max) / running_max
                max_dd = drawdown.min()
                rolling_dd.append(max_dd)
            
            if rolling_dd:
                ax4.plot(df['sell_date'].iloc[window-1:], np.array(rolling_dd) * 100, 
                        linewidth=2, alpha=0.8, label=f'{window}-trade window')
    
    ax4.axhline(y=-20.38, color='red', linestyle='--', linewidth=2, 
               alpha=0.7, label='Baseline Max DD (-20.38%)')
    ax4.axhline(y=-30, color='orange', linestyle=':', alpha=0.7, label='Risk Threshold (-30%)')
    ax4.set_title('📉 Rolling Maximum Drawdown - Risk Monitoring', fontsize=14, fontweight='bold')
    ax4.set_ylabel('Max Drawdown (%)')
    ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax4.grid(True, alpha=0.3)
    
    # Chart 5: Strategy Edge Persistence Score
    ax5 = plt.subplot(3, 2, 5)
    
    # Calculate composite edge score (0-100)
    window = 60  # Use 60-trade window for score
    if len(df) >= window:
        edge_scores = []
        dates_for_scores = []
        
        for i in range(window-1, len(df)):
            window_data = df.iloc[i-window+1:i+1]
            
            # Calculate metrics
            annual_ret = (1 + window_data['net_return']).prod() ** (252/len(window_data)) - 1
            win_rate = (window_data['net_return'] > 0).mean()
            sharpe = (window_data['net_return'].mean() / window_data['net_return'].std()) * np.sqrt(252)
            
            # Calculate scores (0-100)
            ret_score = max(0, min(100, (annual_ret / baseline_annual_return) * 100))
            wr_score = max(0, min(100, (win_rate / baseline_win_rate) * 100))
            sharpe_score = max(0, min(100, (sharpe / baseline_sharpe) * 100))
            
            edge_score = (ret_score + wr_score + sharpe_score) / 3
            edge_scores.append(edge_score)
            dates_for_scores.append(df['sell_date'].iloc[i])
        
        # Plot edge score with color coding
        colors = ['red' if score < 50 else 'orange' if score < 75 else 'green' for score in edge_scores]
        ax5.scatter(dates_for_scores, edge_scores, c=colors, alpha=0.7, s=20)
        ax5.plot(dates_for_scores, edge_scores, 'gray', alpha=0.5, linewidth=1)
        
        # Add trend line
        if len(edge_scores) > 10:
            z = np.polyfit(range(len(edge_scores)), edge_scores, 1)
            p = np.poly1d(z)
            ax5.plot(dates_for_scores, p(range(len(edge_scores))), "black", 
                    linewidth=3, alpha=0.8, label=f'Trend (slope: {z[0]:+.1f}/period)')
    
    ax5.axhline(y=75, color='green', linestyle='--', alpha=0.7, label='Excellent (75+)')
    ax5.axhline(y=50, color='orange', linestyle='--', alpha=0.7, label='Acceptable (50+)')
    ax5.axhline(y=25, color='red', linestyle='--', alpha=0.7, label='Poor (<50)')
    ax5.set_title('🎯 Strategy Edge Persistence Score', fontsize=14, fontweight='bold')
    ax5.set_ylabel('Edge Score (0-100)')
    ax5.set_ylim(0, 100)
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # Chart 6: Performance Trend Analysis
    ax6 = plt.subplot(3, 2, 6)
    
    # Create quarterly performance analysis
    df['quarter'] = df['sell_date'].dt.to_period('Q')
    quarterly_perf = df.groupby('quarter').agg({
        'net_return': ['count', 'mean', lambda x: (x > 0).mean()]
    }).reset_index()
    
    quarterly_perf.columns = ['quarter', 'trades', 'avg_return', 'win_rate']
    quarterly_perf['annual_return'] = ((1 + quarterly_perf['avg_return']) ** (252/63)) - 1  # Approx 63 trading days per quarter
    
    # Plot quarterly trends
    quarters = [str(q) for q in quarterly_perf['quarter']]
    ax6.bar(range(len(quarters)), quarterly_perf['annual_return'] * 100, 
           alpha=0.7, color=['red' if x < 0 else 'green' for x in quarterly_perf['annual_return']])
    ax6.axhline(y=baseline_annual_return * 100, color='red', linestyle='--', 
               linewidth=2, alpha=0.7, label=f'Baseline ({baseline_annual_return:.1%})')
    
    ax6.set_title('📊 Quarterly Performance Trend', fontsize=14, fontweight='bold')
    ax6.set_ylabel('Quarterly Annual Return (%)')
    ax6.set_xticks(range(len(quarters)))
    ax6.set_xticklabels(quarters, rotation=45)
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.subplots_adjust(right=0.85)  # Make room for legends
    
    # Save the comprehensive rolling analysis
    rolling_file = 'results/pdf_charts/rolling_performance_analysis.png'
    plt.savefig(rolling_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"📊 Rolling performance analysis saved: {rolling_file}")
    
    # Create trend summary chart
    create_trend_summary_chart(df)
    
    return rolling_file

def create_trend_summary_chart(df):
    """Create a focused trend summary chart."""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
    
    # Top chart: Portfolio value with trend analysis
    ax1.plot(df['sell_date'], df['portfolio_value'], 'b-', linewidth=2, alpha=0.8, label='Portfolio Value')
    
    # Add trend lines for different periods
    if len(df) > 100:
        # Overall trend
        z_all = np.polyfit(range(len(df)), df['portfolio_value'], 1)
        p_all = np.poly1d(z_all)
        ax1.plot(df['sell_date'], p_all(range(len(df))), 'green', 
                linewidth=3, alpha=0.7, label=f'Overall Trend (${z_all[0]:.0f}/trade)')
        
        # Recent trend (last 120 trades)
        if len(df) >= 120:
            recent_df = df.tail(120)
            z_recent = np.polyfit(range(len(recent_df)), recent_df['portfolio_value'], 1)
            p_recent = np.poly1d(z_recent)
            recent_trend_values = p_recent(range(len(recent_df)))
            ax1.plot(recent_df['sell_date'], recent_trend_values, 'red', 
                    linewidth=3, alpha=0.8, label=f'Recent Trend (${z_recent[0]:.0f}/trade)')
    
    ax1.axhline(y=10000, color='gray', linestyle='--', alpha=0.5, label='Starting Capital')
    ax1.set_title('🎯 Portfolio Growth Trend Analysis', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Portfolio Value ($)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Bottom chart: 90-day rolling return vs baseline
    window = 90
    if len(df) >= window:
        rolling_annual_returns = df['net_return'].rolling(window=window).apply(
            lambda x: (1 + x).prod() ** (252/len(x)) - 1 if len(x) > 0 else np.nan
        )
        
        # Plot with color coding
        dates = df['sell_date'].iloc[window-1:]
        returns = rolling_annual_returns.iloc[window-1:] * 100
        
        colors = ['red' if r < 30 else 'orange' if r < 60 else 'green' for r in returns]
        ax2.scatter(dates, returns, c=colors, alpha=0.6, s=15)
        ax2.plot(dates, returns, 'gray', alpha=0.5, linewidth=1)
        
        # Add baseline and trend
        ax2.axhline(y=72.32, color='blue', linestyle='--', linewidth=2, 
                   alpha=0.8, label='Original Baseline (72.3%)')
        ax2.axhline(y=0, color='black', linestyle=':', alpha=0.5)
        
        # Trend line
        if len(returns.dropna()) > 10:
            valid_returns = returns.dropna()
            z = np.polyfit(range(len(valid_returns)), valid_returns, 1)
            p = np.poly1d(z)
            trend_line = p(range(len(valid_returns)))
            ax2.plot(dates[:len(valid_returns)], trend_line, 'black', 
                    linewidth=3, alpha=0.8, label=f'Trend ({z[0]:+.1f}%/period)')
    
    ax2.set_title(f'📈 {window}-Trade Rolling Annual Returns - Edge Persistence Tracking', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Rolling Annual Return (%)')
    ax2.set_xlabel('Date')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    trend_file = 'results/pdf_charts/strategy_trend_analysis.png'
    plt.savefig(trend_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Monthly returns
    plt.subplot(2, 1, 2)
    trade_results['year_month'] = trade_results['sell_date'].dt.to_period('M')
    monthly_returns = trade_results.groupby('year_month')['net_return'].sum()
    
    colors_list = ['green' if x > 0 else 'red' for x in monthly_returns]
    x_pos = range(len(monthly_returns))
    bars = plt.bar(x_pos, monthly_returns * 100, color=colors_list, alpha=0.7)
    plt.title('Monthly Returns Distribution', fontsize=12, fontweight='bold')
    plt.ylabel('Return (%)')
    plt.xlabel('Month')
    plt.xticks(x_pos[::2], [str(x) for x in monthly_returns.index[::2]], rotation=45)
    plt.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars, monthly_returns * 100):
        if abs(value) > 1:  # Only label significant returns
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (0.5 if value > 0 else -0.5), 
                    f'{value:.1f}%', ha='center', va='bottom' if value > 0 else 'top', fontsize=8)
    
    plt.tight_layout()
    plt.savefig('results/pdf_charts/portfolio_performance.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Strategy Comparison Chart
    # Calculate comparison data
    start_price = trade_results['buy_price'].iloc[0]
    end_price = trade_results['sell_price'].iloc[-1]
    buy_hold_return = (end_price - start_price) / start_price
    
    day_returns = -(trade_results['gross_return'])
    day_total_return = (1 + day_returns).prod() - 1
    
    # Check if SPY analysis is available
    try:
        spy_perf = pd.read_csv('results/ibit_spy_performance.csv')
        spy_return = spy_perf['total_return'].iloc[0]
        has_spy_data = True
    except:
        spy_return = 0
        has_spy_data = False
    
    # Build strategies list based on available data
    strategies = ['Overnight Only', 'Day Only', 'Buy & Hold']
    returns = [performance['total_return'].iloc[0] * 100, day_total_return * 100, buy_hold_return * 100]
    colors_strategy = ['blue', 'red', 'green']
        
    if has_spy_data:
        strategies.append('IBIT + SPY')
        returns.append(spy_return * 100)
        colors_strategy.append('purple')
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(strategies, returns, color=colors_strategy, alpha=0.7)
    plt.title('Strategy Performance Comparison', fontsize=14, fontweight='bold')
    plt.ylabel('Total Return (%)')
    
    # Add value labels
    for bar, value in zip(bars, returns):
        if value >= 0:
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                    f'{value:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)
        else:
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 10, 
                    f'{value:.1f}%', ha='center', va='top', fontweight='bold', fontsize=12, color='white')
    
    plt.grid(True, alpha=0.3)
    
    # Adjust y-axis to accommodate negative values if present
    min_return = min(returns)
    max_return = max(returns)
    if min_return < 0:
        plt.ylim(min_return * 1.2, max_return * 1.2)
    else:
        plt.ylim(0, max_return * 1.2)
    
    # Add a horizontal line at zero if there are negative returns
    if min_return < 0:
        plt.axhline(y=0, color='black', linewidth=1, alpha=0.5)
    plt.savefig('results/pdf_charts/strategy_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Drawdown Analysis
    portfolio_values = trade_results['portfolio_value']
    running_max = portfolio_values.expanding().max()
    drawdowns = (portfolio_values - running_max) / running_max * 100
    
    plt.figure(figsize=(12, 5))
    plt.fill_between(trade_results['sell_date'], drawdowns, 0, color='red', alpha=0.3, label='Drawdown')
    plt.plot(trade_results['sell_date'], drawdowns, 'r-', linewidth=1)
    plt.axhline(y=0, color='black', linewidth=1)
    plt.title('Portfolio Drawdown Analysis', fontsize=14, fontweight='bold')
    plt.ylabel('Drawdown (%)')
    plt.xlabel('Date')
    plt.grid(True, alpha=0.3)
    plt.savefig('results/pdf_charts/drawdown_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. Returns Distribution
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.hist(trade_results['net_return'] * 100, bins=30, alpha=0.7, color='blue', edgecolor='black')
    plt.title('Trade Returns Distribution', fontweight='bold')
    plt.xlabel('Return (%)')
    plt.ylabel('Frequency')
    plt.grid(True, alpha=0.3)
    plt.axvline(x=0, color='red', linestyle='--', alpha=0.7)
    
    plt.subplot(1, 2, 2)
    colors_scatter = ['green' if x > 0 else 'red' for x in trade_results['net_return']]
    plt.scatter(range(len(trade_results)), trade_results['net_return'] * 100, 
               c=colors_scatter, alpha=0.6, s=10)
    plt.title('Returns Over Time', fontweight='bold')
    plt.xlabel('Trade Number')
    plt.ylabel('Return (%)')
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color='black', linewidth=1)
    
    plt.tight_layout()
    plt.savefig('results/pdf_charts/returns_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ All charts created successfully!")
    
    return {
        'portfolio_performance': 'results/pdf_charts/portfolio_performance.png',
        'strategy_comparison': 'results/pdf_charts/strategy_comparison.png',
        'drawdown_analysis': 'results/pdf_charts/drawdown_analysis.png',
        'returns_distribution': 'results/pdf_charts/returns_distribution.png'
    }

def create_pdf_report():
    """Create comprehensive PDF report."""
    
    print("📄 Creating PDF Report...")
    
    # Create charts first
    chart_files = create_charts()
    
    # Load data
    trade_results = pd.read_csv('results/trade_results.csv')
    performance = pd.read_csv('results/performance_summary.csv')
    
    # Calculate additional metrics
    start_price = trade_results['buy_price'].iloc[0]
    end_price = trade_results['sell_price'].iloc[-1]
    buy_hold_return = (end_price - start_price) / start_price
    
    day_returns = -(trade_results['gross_return'])
    day_total_return = (1 + day_returns).prod() - 1
    
    # Create PDF
    doc = SimpleDocTemplate("results/IBIT_Strategy_Analysis_Report.pdf", pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.darkblue,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.darkblue,
        spaceAfter=12,
        spaceBefore=20
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.darkblue,
        spaceAfter=6,
        spaceBefore=12
    )
    
    # Title Page
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph("IBIT Overnight Trading Strategy", title_style))
    story.append(Paragraph("Comprehensive Analysis Report", title_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Load SPY performance for summary if available
    spy_summary_data = None
    try:
        spy_perf_summary = pd.read_csv('results/ibit_spy_performance.csv')
        spy_summary_data = spy_perf_summary.iloc[0]
    except:
        spy_summary_data = None
    
    # Executive Summary Box - use enhanced strategy if available
    if spy_summary_data is not None:
        # Use SPY enhanced results for summary
        summary_data = [
            ['Metric', 'IBIT Only', 'IBIT + SPY'],
            ['Analysis Period', 'Jan 2024 - Dec 2025', 'Jan 2024 - Dec 2025'],
            ['Total Return', f"{performance['total_return'].iloc[0]:.1%}", f"{spy_summary_data['total_return']:.1%}"],
            ['Annualized Return', f"{performance['annualized_return'].iloc[0]:.1%}", f"{spy_summary_data['annualized_return']:.1%}"],
            ['Sharpe Ratio', f"{performance['sharpe_ratio'].iloc[0]:.2f}", f"{spy_summary_data['sharpe_ratio']:.2f}"],
            ['Win Rate', f"{performance['win_rate'].iloc[0]:.1%}", f"{spy_summary_data['win_rate']:.1%}"],
            ['Max Drawdown', f"{performance['max_drawdown'].iloc[0]:.1%}", f"{spy_summary_data['max_drawdown']:.1%}"],
            ['Total Trades', f"{len(trade_results):,}", f"{spy_summary_data['spy_trading_days']:.0f} SPY + {len(trade_results):,} IBIT"],
        ]
    else:
        # Use original IBIT-only results
        summary_data = [
            ['Metric', 'Value'],
            ['Analysis Period', 'January 11, 2024 - December 12, 2025'],
            ['Total Return', f"{performance['total_return'].iloc[0]:.1%}"],
            ['Annualized Return', f"{performance['annualized_return'].iloc[0]:.1%}"],
            ['Sharpe Ratio', f"{performance['sharpe_ratio'].iloc[0]:.2f}"],
            ['Win Rate', f"{performance['win_rate'].iloc[0]:.1%}"],
            ['Max Drawdown', f"{performance['max_drawdown'].iloc[0]:.1%}"],
            ['Total Trades', f"{len(trade_results):,}"],
        ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch] if spy_summary_data is None else [2.5*inch, 2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12 if spy_summary_data is None else 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.5*inch))
    
    # Key Insights
    story.append(Paragraph("Key Findings", subtitle_style))
    insights = [
        "• Strategy generates 72.3% annual returns with excellent risk-adjusted performance",
        "• Significantly outperforms both day-trading (-52.6%) and buy-and-hold (47.0%)",
        "• Sharpe ratio of 1.81 indicates superior risk-adjusted returns",
        "• 54.7% win rate demonstrates consistent edge in overnight Bitcoin movements",
        "• SPY day trading strategy validated as viable enhancement (+6.9% annual improvement)",
        "• Ready for Alpaca implementation with realistic commission-free cost assumptions"
    ]
    
    for insight in insights:
        story.append(Paragraph(insight, styles['Normal']))
    
    story.append(PageBreak())
    
    # Strategy Overview
    story.append(Paragraph("Strategy Overview", subtitle_style))
    
    overview_text = """
    The IBIT Overnight Trading Strategy is designed to capture overnight price movements in the iShares Bitcoin Trust ETF (IBIT). 
    The strategy operates on a simple premise: buy IBIT at market close (4:00 PM ET) and sell at market open (9:30 AM ET) the following trading day.
    
    This approach aims to capitalize on Bitcoin's tendency to exhibit significant price movements during overnight hours, 
    when traditional U.S. markets are closed but global cryptocurrency trading continues 24/7.
    """
    
    story.append(Paragraph(overview_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Strategy Rules
    story.append(Paragraph("Trading Rules", heading_style))
    rules_data = [
        ['Rule', 'Description'],
        ['Entry', 'Buy IBIT at market close (4:00 PM ET)'],
        ['Exit', 'Sell IBIT at market open (9:30 AM ET) next day'],
        ['Position Size', '100% of available capital'],
        ['Trading Costs', '0.01% slippage (commission-free assumed)'],
        ['Risk Management', 'Daily exit, no overnight risk accumulation'],
    ]
    
    rules_table = Table(rules_data, colWidths=[2*inch, 4*inch])
    rules_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(rules_table)
    story.append(PageBreak())
    
    # Performance Analysis
    story.append(Paragraph("Performance Analysis", subtitle_style))
    
    # Portfolio Performance Chart
    story.append(Paragraph("Portfolio Performance Over Time", heading_style))
    story.append(Image(chart_files['portfolio_performance'], width=7*inch, height=5.6*inch))
    story.append(Spacer(1, 20))
    
    # Rolling Performance Trend Analysis
    story.append(Paragraph("Rolling Performance Trend Analysis", heading_style))
    
    rolling_analysis_text = """
    <b>Strategy Edge Persistence Analysis:</b><br/>
    The following charts analyze whether the IBIT overnight edge is persisting or decaying over time 
    by examining rolling performance metrics across different time windows. This analysis is critical 
    for detecting market regime changes and strategy degradation.<br/><br/>
    
    <b>Key Insights from Rolling Analysis:</b><br/>
    • <b>Rolling Returns:</b> Tracks annualized returns across moving windows vs 72.3% baseline<br/>
    • <b>Win Rate Consistency:</b> Monitors success rate vs 54.7% baseline over time<br/>
    • <b>Risk-Adjusted Performance:</b> Sharpe ratio trends vs 1.81 baseline<br/>
    • <b>Edge Persistence Score:</b> Composite metric (0-100) combining all factors<br/>
    • <b>Trend Direction:</b> Statistical trend analysis to detect acceleration/deceleration<br/><br/>
    
    <b>Color Coding:</b> Green = Strong edge, Orange = Moderate edge, Red = Edge degradation
    """
    
    story.append(Paragraph(rolling_analysis_text, styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Add rolling performance charts
    try:
        story.append(Image('results/pdf_charts/rolling_performance_analysis.png', width=7.5*inch, height=9.6*inch))
        story.append(Spacer(1, 20))
        
        # Add trend summary chart
        story.append(Paragraph("Strategy Trend Summary", heading_style))
        
        trend_summary_text = """
        <b>Focused Trend Analysis:</b><br/>
        This analysis focuses on the most critical trend indicators for edge persistence detection:
        portfolio growth trajectory and 90-day rolling returns vs baseline performance.
        """
        
        story.append(Paragraph(trend_summary_text, styles['Normal']))
        story.append(Spacer(1, 10))
        
        story.append(Image('results/pdf_charts/strategy_trend_analysis.png', width=7*inch, height=6*inch))
        story.append(Spacer(1, 20))
        
    except FileNotFoundError:
        story.append(Paragraph("Rolling performance charts will be generated when data is available.", styles['Normal']))
        story.append(Spacer(1, 20))
    
    # Strategy Comparison
    story.append(Paragraph("Strategy Comparison", heading_style))
    
    # Load SPY analysis if available
    spy_performance = None
    try:
        spy_perf_data = pd.read_csv('results/ibit_spy_performance.csv')
        spy_performance = spy_perf_data.iloc[0]
    except:
        spy_performance = None
    
    comparison_data = [
        ['Strategy', 'Total Return', 'Annualized Return', 'Key Characteristics'],
        ['Overnight Only', f"{performance['total_return'].iloc[0]:.1%}", f"{performance['annualized_return'].iloc[0]:.1%}", 'Captures overnight Bitcoin movements'],
        ['Day Only', f"{day_total_return:.1%}", f"{(1 + day_total_return)**(1/1.92)-1:.1%}", 'Trades during market hours only'],
        ['Buy & Hold', f"{buy_hold_return:.1%}", f"{(1 + buy_hold_return)**(1/1.92)-1:.1%}", 'Passive investment approach'],
    ]
    
    # Add SPY analysis if available
    if spy_performance is not None:
        comparison_data.append([
            'IBIT + SPY', 
            f"{spy_performance['total_return']:.1%}", 
            f"{spy_performance['annualized_return']:.1%}", 
            'IBIT overnight + SPY day trading'
        ])
    
    comparison_table = Table(comparison_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 2.5*inch])
    comparison_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(comparison_table)
    story.append(Spacer(1, 15))
    
    # Add SPY analysis explanation if available
    if spy_performance is not None:
        story.append(Paragraph("SPY Day Trading Strategy Analysis", heading_style))
        
        spy_analysis_text = f"""
        <b>IBIT + SPY Day Trading Strategy Results:</b><br/>
        Analysis of combining IBIT overnight trades with SPY day trading during market hours 
        shows promising results as a viable strategy enhancement:<br/><br/>
        
        • <b>Combined Performance:</b> {spy_performance['annualized_return']:.1%} annual return<br/>
        • <b>SPY Day Trading Contribution:</b> {spy_performance['spy_contribution_annual']:+.1%} annual addition<br/>
        • <b>SPY Win Rate:</b> {spy_performance['spy_win_rate']:.1%} (modest edge over random)<br/>
        • <b>Transaction Cost Impact:</b> Minimal due to SPY's tight spreads (0.004% per round trip)<br/>
        • <b>Risk-Adjusted Performance:</b> Sharpe ratio {spy_performance['sharpe_ratio']:.2f} (excellent)<br/><br/>
        
        <b>Key Finding:</b> SPY day trading successfully adds {spy_performance['spy_contribution_annual']:.1%} 
        annual returns with manageable risk increase. The strategy benefits from SPY's exceptional 
        liquidity and tight spreads, making transaction costs negligible relative to potential gains.<br/><br/>
        
        <b>Implementation Feasibility:</b> Requires 4 daily trades vs 2, but execution is systematic:
        9:35 AM sell IBIT → buy SPY, 3:55 PM sell SPY → buy IBIT. SPY's high liquidity ensures 
        reliable execution at predicted costs.<br/><br/>
        
        <b>Recommendation:</b> SPY day trading represents a viable strategy enhancement, offering 
        meaningful additional returns ({spy_performance['spy_contribution_annual']:+.1%}) with acceptable 
        complexity increase and strong risk-adjusted performance.
        """
        
        story.append(Paragraph(spy_analysis_text, styles['Normal']))
        story.append(Spacer(1, 15))
    story.append(Image(chart_files['strategy_comparison'], width=6*inch, height=3.6*inch))
    
    story.append(PageBreak())
    
    # Risk Analysis
    story.append(Paragraph("Risk Analysis", subtitle_style))
    
    # Risk Metrics Table
    risk_data = [
        ['Risk Metric', 'Value', 'Interpretation'],
        ['Volatility (Annual)', f"{performance['volatility'].iloc[0]:.1%}", 'High but typical for crypto strategies'],
        ['Sharpe Ratio', f"{performance['sharpe_ratio'].iloc[0]:.2f}", 'Excellent risk-adjusted returns'],
        ['Maximum Drawdown', f"{performance['max_drawdown'].iloc[0]:.1%}", 'Manageable for high-return strategy'],
        ['Calmar Ratio', f"{performance['calmar_ratio'].iloc[0]:.2f}", 'Strong return vs. drawdown ratio'],
        ['Win Rate', f"{performance['win_rate'].iloc[0]:.1%}", 'Above 50% indicates edge'],
    ]
    
    risk_table = Table(risk_data, colWidths=[2*inch, 1.5*inch, 3*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(risk_table)
    story.append(Spacer(1, 15))
    
    # Drawdown Chart
    story.append(Paragraph("Drawdown Analysis", heading_style))
    story.append(Image(chart_files['drawdown_analysis'], width=7*inch, height=2.9*inch))
    
    story.append(PageBreak())
    
    # Trade Analysis
    story.append(Paragraph("Trade Analysis", subtitle_style))
    
    # Trade Statistics
    trade_stats_data = [
        ['Statistic', 'Value'],
        ['Total Trades', f"{len(trade_results):,}"],
        ['Winning Trades', f"{(trade_results['net_return'] > 0).sum():,}"],
        ['Losing Trades', f"{(trade_results['net_return'] < 0).sum():,}"],
        ['Average Return per Trade', f"{trade_results['net_return'].mean():.3%}"],
        ['Best Trade', f"{trade_results['net_return'].max():.2%}"],
        ['Worst Trade', f"{trade_results['net_return'].min():.2%}"],
        ['Average Win', f"{trade_results[trade_results['net_return'] > 0]['net_return'].mean():.2%}"],
        ['Average Loss', f"{trade_results[trade_results['net_return'] < 0]['net_return'].mean():.2%}"],
    ]
    
    trade_stats_table = Table(trade_stats_data, colWidths=[3*inch, 2*inch])
    trade_stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(trade_stats_table)
    story.append(Spacer(1, 15))
    
    # Returns Distribution Chart
    story.append(Image(chart_files['returns_distribution'], width=7*inch, height=2.9*inch))
    
    story.append(PageBreak())
    
    # Implementation Guide
    story.append(Paragraph("Implementation Guide", subtitle_style))
    
    implementation_text = """
    <b>Alpaca Trading Platform Readiness:</b><br/>
    The strategy has been designed and backtested with realistic assumptions for implementation on the Alpaca trading platform:
    
    • <b>Commission-Free Trading:</b> No commission costs assumed (realistic for Alpaca)<br/>
    • <b>Minimal Slippage:</b> 0.01% slippage cost for IBIT (highly liquid ETF)<br/>
    • <b>Systematic Execution:</b> Clear rules suitable for API automation<br/>
    • <b>Risk Management:</b> Daily exits limit overnight risk accumulation<br/><br/>
    
    <b>Implementation Steps:</b><br/>
    1. Set up Alpaca API access and paper trading environment<br/>
    2. Implement automated buy orders at market close (4:00 PM ET)<br/>
    3. Implement automated sell orders at market open (9:30 AM ET)<br/>
    4. Start with smaller position sizes to validate live performance<br/>
    5. Monitor strategy performance vs. backtested expectations<br/><br/>
    
    <b>Risk Considerations:</b><br/>
    • High volatility (38.8% annually) requires appropriate risk tolerance<br/>
    • Maximum drawdown of 20.4% could test investor patience<br/>
    • Strategy performance is dependent on Bitcoin market conditions<br/>
    • Overnight patterns may diminish over time as markets adapt<br/>
    """
    
    story.append(Paragraph(implementation_text, styles['Normal']))
    
    story.append(PageBreak())
    
    # Conclusions
    story.append(Paragraph("Conclusions", subtitle_style))
    
    conclusions_text = """
    <b>Strategy Viability:</b><br/>
    The IBIT Overnight Trading Strategy demonstrates exceptional performance with realistic trading costs, 
    generating 72.3% annualized returns with a Sharpe ratio of 1.81. Analysis of potential enhancements 
    reveals a viable path for improved returns through careful strategy combination.<br/><br/>
    
    <b>Strategy Enhancement Analysis:</b><br/>
    <b>SPY Day Trading Strategy (Validated):</b> Successfully tested SPY day trading enhancement shows +6.9% 
    annual improvement (79.2% vs 72.3% IBIT-only). SPY's exceptional liquidity and tight spreads (0.004% round trip) 
    make transaction costs negligible while capturing meaningful intraday movements. The enhanced strategy 
    maintains excellent risk-adjusted performance with a Sharpe ratio of 1.83.<br/><br/>
    
    <b>Key Success Factors:</b><br/>
    • <b>Market Inefficiency:</b> Captures overnight Bitcoin price movements not reflected in day trading<br/>
    • <b>Cost Efficiency:</b> Commission-free trading makes high-frequency strategy viable<br/>
    • <b>Risk Management:</b> Daily exits prevent overnight risk accumulation<br/>
    • <b>Systematic Approach:</b> Clear rules eliminate emotional decision-making<br/>
    • <b>Enhancement Potential:</b> SPY day trading adds meaningful returns with controlled risk<br/><br/>
    
    <b>Recommendation:</b><br/>
    Two viable implementation paths: (1) Core IBIT overnight strategy (72.3% annual, lower complexity) 
    or (2) Enhanced IBIT+SPY strategy (79.2% annual, moderate complexity increase). Both approaches 
    are suitable for Alpaca implementation with systematic execution rules.<br/><br/>
    
    <b>Next Steps:</b><br/>
    Begin with core IBIT strategy implementation, then consider SPY enhancement after validating 
    live performance. Paper trading recommended for 2 weeks before live implementation of enhanced strategy.
    """
    
    story.append(Paragraph(conclusions_text, styles['Normal']))
    
    story.append(PageBreak())
    
    # Monthly Monitoring System Section
    story.append(Paragraph("7. Monthly Monitoring System", subtitle_style))
    story.append(Spacer(1, 20))
    
    monitoring_intro_text = """
    <b>Automated Edge Persistence Monitoring</b><br/><br/>
    
    A comprehensive monitoring system has been developed to track strategy performance on an ongoing basis and detect 
    edge degradation before significant losses occur. This system addresses the critical question: 
    <i>"Does the IBIT overnight edge persist over time?"</i>
    """
    
    story.append(Paragraph(monitoring_intro_text, styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Monitoring Components
    story.append(Paragraph("System Components", heading_style))
    
    components_data = [
        ['Component', 'Purpose', 'Key Features'],
        ['Monthly Monitor', 'Core analysis engine', '• 90-day rolling performance vs baseline\n• Automated performance flags\n• Executive summaries'],
        ['Historical Tracker', 'Long-term trend analysis', '• Multi-month performance history\n• Edge persistence calculation\n• Performance consistency metrics'],
        ['Monthly Check Script', 'Complete workflow', '• One-command execution\n• Automated reporting\n• Result organization']
    ]
    
    components_table = Table(components_data, colWidths=[1.8*inch, 2.2*inch, 2.8*inch])
    components_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    
    story.append(components_table)
    story.append(Spacer(1, 20))
    
    # Key Monitoring Metrics
    story.append(Paragraph("Key Monitoring Metrics", heading_style))
    
    metrics_text = """
    <b>Performance Baselines for Comparison:</b><br/>
    • Annual Return: 72.3% (target: maintain >70%)<br/>
    • Sharpe Ratio: 1.81 (target: maintain >1.5)<br/>
    • Win Rate: 54.7% (target: maintain >50%)<br/>
    • Max Drawdown: -20.4% (alert if exceeds -25%)<br/><br/>
    
    <b>Edge Persistence Metrics:</b><br/>
    • <b>Persistence Rate:</b> Percentage of months outperforming baseline<br/>
    • <b>Consistency Score:</b> Percentage of months within 2% of baseline performance<br/>
    • <b>Performance Volatility:</b> Standard deviation of monthly returns<br/>
    • <b>Trend Analysis:</b> Rolling performance metrics and degradation detection<br/><br/>
    
    <b>Automated Alert Conditions:</b><br/>
    • Return drops >10% below baseline (red flag)<br/>
    • Sharpe ratio falls below 1.0 (performance concern)<br/>
    • Win rate drops below 45% (edge deterioration)<br/>
    • Max drawdown exceeds -30% (risk management)<br/>
    • 3+ consecutive months underperforming (trend reversal)
    """
    
    story.append(Paragraph(metrics_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Usage Instructions
    story.append(Paragraph("Monthly Monitoring Workflow", heading_style))
    
    workflow_text = """
    <b>Recommended Monthly Process:</b><br/><br/>
    
    <b>1. Execute Monthly Check (5 minutes):</b><br/>
    <font name="Courier">python run_monthly_check.py</font><br/><br/>
    
    <b>2. Review Executive Summary:</b><br/>
    • Current performance vs baseline (72.3% annual, 1.81 Sharpe)<br/>
    • Performance flags and concerns<br/>
    • Edge persistence rate assessment<br/><br/>
    
    <b>3. Analyze Detailed Reports:</b><br/>
    • Monthly performance report (JSON)<br/>
    • Historical performance dashboard (PNG)<br/>
    • Trade pattern analysis<br/><br/>
    
    <b>4. Action Based on Results:</b><br/>
    • <font color="green"><b>Strong Edge (>70% persistence):</b></font> Continue strategy as planned<br/>
    • <font color="orange"><b>Moderate Edge (50-70%):</b></font> Monitor closely, consider position size reduction<br/>
    • <font color="red"><b>Weak Edge (<50%):</b></font> Investigate strategy modifications or pause trading
    """
    
    story.append(Paragraph(workflow_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Progressive Intelligence
    story.append(Paragraph("Progressive Monitoring Intelligence", heading_style))
    
    intelligence_data = [
        ['Time Period', 'Analysis Capability', 'Key Insights'],
        ['Months 1-2', 'Basic performance tracking', 'Establish monitoring baseline'],
        ['Months 3-5', 'Trend analysis begins', 'Early edge persistence assessment'],
        ['Months 6-11', 'Statistical edge evaluation', 'Quantitative degradation detection'],
        ['Months 12+', 'Annual performance review', 'Strategy optimization recommendations']
    ]
    
    intelligence_table = Table(intelligence_data, colWidths=[1.5*inch, 2.5*inch, 2.8*inch])
    intelligence_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgreen])
    ]))
    
    story.append(intelligence_table)
    story.append(Spacer(1, 20))
    
    # Visual Dashboard Capabilities
    story.append(Paragraph("Enhanced Visual Dashboard System", heading_style))
    
    visual_dashboard_text = """
    <b>Comprehensive Visual Analytics:</b><br/>
    The monitoring system generates professional-grade visual dashboards to provide instant insights 
    into strategy performance, trends, and risk metrics. All charts are saved as high-resolution PNG files 
    suitable for professional reporting.<br/><br/>
    
    <b>Main Performance Dashboard (6-Panel View):</b><br/>
    • <b>Cumulative Returns:</b> Strategy performance trajectory vs breakeven<br/>
    • <b>Rolling Metrics:</b> Win rate and return trends vs baseline targets<br/>
    • <b>Performance vs Baseline:</b> Side-by-side metric comparison with baseline<br/>
    • <b>Return Distribution:</b> Trade outcome analysis with statistical overlays<br/>
    • <b>Drawdown Analysis:</b> Risk visualization with baseline comparison<br/>
    • <b>Performance Score Card:</b> Quantified performance grading (0-100 scale)<br/><br/>
    
    <b>Detailed Analysis Charts:</b><br/>
    • <b>Trade Timeline Analysis:</b> Individual trade performance patterns<br/>
    • <b>Risk Analysis Dashboard:</b> Multi-panel risk assessment<br/>
    • <b>Win/Loss Streak Analysis:</b> Pattern recognition and consistency metrics<br/>
    • <b>Monthly Performance Heatmap:</b> Calendar-based performance visualization<br/><br/>
    
    <b>Visual Alert System:</b><br/>
    Performance is automatically color-coded and scored for instant assessment:<br/>
    • <font color="green"><b>🟢 EXCELLENT (75-100):</b></font> Strategy performing above expectations<br/>
    • <font color="orange"><b>🟡 GOOD (60-74):</b></font> Meeting baseline expectations<br/>
    • <font color="orange"><b>🟠 FAIR (40-59):</b></font> Some performance concerns detected<br/>
    • <font color="red"><b>🔴 POOR (0-39):</b></font> Immediate attention required<br/><br/>
    
    <b>Automated Chart Generation:</b><br/>
    Running <font name="Courier">python run_monthly_check.py</font> automatically generates:<br/>
    • Main performance dashboard (performance_dashboard_YYYY-MM-DD.png)<br/>
    • Trade timeline analysis (trade_timeline_YYYY-MM-DD.png)<br/>
    • Risk analysis dashboard (risk_analysis_YYYY-MM-DD.png)<br/>
    • Historical trends dashboard (when sufficient data available)<br/><br/>
    
    All visualizations include professional formatting, statistical annotations, baseline comparisons, 
    and institutional-quality presentation suitable for investment reporting.
    """
    
    story.append(Paragraph(visual_dashboard_text, styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Visual Workflow Table
    visual_workflow_data = [
        ['Chart Type', 'Purpose', 'Key Visual Elements'],
        ['Performance Dashboard', '6-panel overview', 'Cumulative returns, rolling metrics,\nbaseline comparisons, score cards'],
        ['Trade Timeline', 'Individual trade analysis', 'Trade-by-trade performance,\nwin/loss streak patterns'],
        ['Risk Analysis', 'Risk assessment', 'Volatility trends, drawdown analysis,\nrisk-adjusted returns'],
        ['Historical Trends', 'Long-term patterns', 'Multi-month trends, edge persistence,\nperformance evolution']
    ]
    
    visual_workflow_table = Table(visual_workflow_data, colWidths=[1.8*inch, 2*inch, 2.8*inch])
    visual_workflow_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightblue])
    ]))
    
    story.append(visual_workflow_table)
    story.append(Spacer(1, 20))
    
    # Current Monitoring Results Section
    story.append(Paragraph("Current Strategy Monitoring Results", heading_style))
    
    # Load actual monitoring results
    import json
    try:
        with open('results/actual_monitoring_results.json', 'r') as f:
            monitoring_results = json.load(f)
        
        current_monitoring_text = f"""
        <b>Analysis Date:</b> {monitoring_results['analysis_date']}<br/>
        <b>Data Period:</b> {monitoring_results['data_period']}<br/>
        <b>Total Trades Analyzed:</b> {monitoring_results['total_trades_analyzed']:,}<br/>
        <b>Recent Period:</b> Last {monitoring_results['recent_period_days']} trades<br/><br/>
        
        <b>Current Performance Metrics:</b><br/>
        • <b>Annual Return:</b> {monitoring_results['current_performance']['annual_return']:.1%}<br/>
        • <b>Sharpe Ratio:</b> {monitoring_results['current_performance']['sharpe_ratio']:.2f}<br/>
        • <b>Win Rate:</b> {monitoring_results['current_performance']['win_rate']:.1%}<br/>
        • <b>Max Drawdown:</b> {monitoring_results['current_performance']['max_drawdown']:.1%}<br/>
        • <b>Portfolio Value:</b> ${monitoring_results['current_performance']['final_portfolio_value']:,.0f}<br/><br/>
        
        <b>Performance vs Baseline:</b><br/>
        • <b>Annual Return:</b> {monitoring_results['baseline_comparison']['annual_return_vs_baseline']}<br/>
        • <b>Sharpe Ratio:</b> {monitoring_results['baseline_comparison']['sharpe_vs_baseline']}<br/>
        • <b>Win Rate:</b> {monitoring_results['baseline_comparison']['win_rate_vs_baseline']}<br/>
        • <b>Return Difference:</b> {monitoring_results['baseline_comparison']['return_difference']:+.1%}<br/>
        • <b>Sharpe Difference:</b> {monitoring_results['baseline_comparison']['sharpe_difference']:+.2f}<br/>
        • <b>Win Rate Difference:</b> {monitoring_results['baseline_comparison']['win_rate_difference']:+.1%}<br/><br/>
        
        <b>Performance Assessment:</b><br/>
        <b>Overall Score:</b> {monitoring_results['performance_score']['overall_score']:.0f}/100<br/>
        <b>Status:</b> {monitoring_results['assessment']}<br/><br/>
        """
        
        story.append(Paragraph(current_monitoring_text, styles['Normal']))
        
        # Performance Flags
        if monitoring_results['performance_flags']:
            story.append(Paragraph("Performance Flags Detected:", heading_style))
            
            flags_text = f"""
            <b>Current Alerts ({len(monitoring_results['performance_flags'])} flags detected):</b><br/>
            """
            
            for flag in monitoring_results['performance_flags']:
                # Clean up emoji that might not render in PDF
                clean_flag = flag.replace('🔴', '[RED]').replace('🟡', '[YELLOW]').replace('🟠', '[ORANGE]')
                flags_text += f"• {clean_flag}<br/>"
            
            story.append(Paragraph(flags_text, styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Recommendations  
        if monitoring_results['recommendations']:
            story.append(Paragraph("Current Recommendations:", heading_style))
            
            rec_text = f"""
            <b>Immediate Actions Required ({len(monitoring_results['recommendations'])} recommendations):</b><br/>
            """
            
            for rec in monitoring_results['recommendations'][:6]:  # Show top 6
                # Clean up emoji
                clean_rec = (rec.replace('✅', '[CHECK]').replace('🟡', '[YELLOW]')
                           .replace('⚠️', '[WARNING]').replace('🚨', '[ALERT]')
                           .replace('💰', '[MONEY]').replace('📅', '[CALENDAR]')
                           .replace('📈', '[CHART]').replace('📉', '[DOWN]')
                           .replace('⏸️', '[PAUSE]').replace('🔍', '[SEARCH]')
                           .replace('🔬', '[RESEARCH]').replace('🔴', '[RED]')
                           .replace('📊', '[ANALYSIS]'))
                rec_text += f"• {clean_rec}<br/>"
            
            story.append(Paragraph(rec_text, styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Performance Score Breakdown
        score_table_data = [
            ['Metric', 'Score', 'Status'],
            ['Return Performance', f"{monitoring_results['performance_score']['return_score']:.0f}/100", 
             'Poor' if monitoring_results['performance_score']['return_score'] < 50 else 'Good'],
            ['Sharpe Performance', f"{monitoring_results['performance_score']['sharpe_score']:.0f}/100",
             'Poor' if monitoring_results['performance_score']['sharpe_score'] < 50 else 'Good'],
            ['Win Rate Performance', f"{monitoring_results['performance_score']['win_rate_score']:.0f}/100",
             'Poor' if monitoring_results['performance_score']['win_rate_score'] < 50 else 'Good'],
            ['Overall Score', f"{monitoring_results['performance_score']['overall_score']:.0f}/100", 
             'Critical' if monitoring_results['performance_score']['overall_score'] < 40 else 'Acceptable']
        ]
        
        score_table = Table(score_table_data, colWidths=[2.2*inch, 1.5*inch, 1.8*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        story.append(score_table)
        story.append(Spacer(1, 20))
        
        # Critical Analysis
        critical_analysis_text = f"""
        <b>Critical Analysis Summary:</b><br/>
        The current monitoring results indicate <b>significant performance degradation</b> from the original strategy 
        baseline established during the backtesting period. Key concerns include:<br/><br/>
        
        • <b>Return Performance:</b> Current annualized return of {monitoring_results['current_performance']['annual_return']:.1%} 
        is substantially below the baseline target of 72.3%<br/>
        • <b>Risk Profile:</b> Sharpe ratio of {monitoring_results['current_performance']['sharpe_ratio']:.2f} indicates 
        poor risk-adjusted returns compared to baseline of 1.81<br/>
        • <b>Consistency:</b> Win rate of {monitoring_results['current_performance']['win_rate']:.1%} has declined 
        from baseline of 54.7%<br/><br/>
        
        <b>Potential Causes:</b><br/>
        • Market regime change affecting Bitcoin overnight patterns<br/>
        • Increased institutional participation altering overnight premiums<br/>
        • Macroeconomic factors impacting Bitcoin volatility patterns<br/>
        • Strategy capacity constraints as more capital employs similar approaches<br/><br/>
        
        <b>Immediate Actions:</b><br/>
        Given the severity of performance degradation, immediate portfolio protection measures should be implemented 
        while conducting comprehensive analysis of market regime changes.
        """
        
        story.append(Paragraph(critical_analysis_text, styles['Normal']))
        
    except FileNotFoundError:
        story.append(Paragraph("Monitoring results not yet available. Run monthly monitoring analysis to generate current performance data.", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Integration with Trading
    story.append(Paragraph("Integration with Live Trading", heading_style))
    
    integration_text = """
    <b>Risk Management Integration:</b><br/>
    The monitoring system is designed to protect capital by providing early warning signals before significant 
    edge degradation impacts performance. Key risk management features include:<br/><br/>
    
    • <b>Position Sizing Guidance:</b> Adjust position sizes based on recent performance consistency<br/>
    • <b>Strategy Pause Triggers:</b> Clear criteria for temporarily halting trading<br/>
    • <b>Performance Verification:</b> Monthly validation that the overnight premium persists<br/>
    • <b>Market Regime Detection:</b> Identify when market conditions may have changed<br/><br/>
    
    <b>Expected Evolution:</b><br/>
    As monitoring data accumulates, the system will become increasingly sophisticated at detecting 
    subtle changes in market behavior that could impact strategy performance. The goal is to maintain 
    the strategy's edge while adapting to evolving market conditions.
    """
    
    story.append(Paragraph(integration_text, styles['Normal']))
    story.append(Spacer(1, 30))
    
    # Footer
    footer_text = f"""
    <i>This analysis is for educational purposes only and does not constitute financial advice. 
    Past performance does not guarantee future results. Trading involves substantial risk of loss.</i><br/><br/>
    
    Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
    Core analysis: {len(trade_results):,} IBIT trades from January 11, 2024 to December 12, 2025<br/>
    Enhancement testing: SPY day trading strategy validated as viable improvement
    """
    
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    
    print("✅ PDF report created: results/IBIT_Strategy_Analysis_Report.pdf")
    
    return "results/IBIT_Strategy_Analysis_Report.pdf"

if __name__ == "__main__":
    pdf_file = create_pdf_report()
    print(f"🎉 Comprehensive PDF report generated successfully!")
    print(f"📁 Location: {pdf_file}")
    print(f"📄 Open the file to view the complete analysis with charts and detailed findings.")