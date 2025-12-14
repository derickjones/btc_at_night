"""
Comprehensive Summary Report Generator for IBIT Trading Strategy Analysis.
Creates detailed HTML report with performance graphs and strategy comparisons.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

# Add src directory to path
sys.path.append('src')
from visualization import StrategyVisualizer
from strategy_comparison import StrategyComparer
import config

def create_html_report():
    """Create comprehensive HTML report."""
    
    print("📄 Generating Comprehensive Summary Report...")
    print("=" * 60)
    
    # Run strategy comparisons first
    comparer = StrategyComparer()
    comparison_results = comparer.run_all_comparisons()
    
    # Create visualizations
    visualizer = StrategyVisualizer()
    charts = visualizer.create_all_visualizations()
    
    # Load all performance data
    overnight_perf = pd.read_csv('results/performance_summary.csv')
    comparison_df = pd.read_csv('results/strategy_comparison.csv')
    
    # Start HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>IBIT Overnight Trading Strategy - Comprehensive Analysis Report</title>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 40px;
                line-height: 1.6;
                color: #333;
            }}
            .header {{
                text-align: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
            }}
            .section {{
                margin: 30px 0;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .metric-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .metric-value {{
                font-size: 2em;
                font-weight: bold;
                color: #2c5aa0;
            }}
            .metric-label {{
                color: #666;
                margin-top: 10px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #4CAF50;
                color: white;
            }}
            .positive {{ color: #2E7D32; font-weight: bold; }}
            .negative {{ color: #C62828; font-weight: bold; }}
            .chart-container {{
                margin: 30px 0;
                text-align: center;
            }}
            .highlight {{
                background-color: #fff3cd;
                padding: 15px;
                border-radius: 5px;
                border-left: 4px solid #ffc107;
                margin: 20px 0;
            }}
            .conclusions {{
                background-color: #d1ecf1;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #17a2b8;
                margin: 30px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏦 IBIT Overnight Trading Strategy</h1>
            <h2>Comprehensive Analysis Report</h2>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p>Analysis Period: {overnight_perf['start_date'].iloc[0]} to {overnight_perf['end_date'].iloc[0]}</p>
        </div>

        <div class="section">
            <h2>📋 Executive Summary</h2>
            <div class="highlight">
                <h3>Strategy Overview</h3>
                <ul>
                    <li><strong>Approach:</strong> Buy IBIT at market close (4:00 PM ET), sell at market open (9:30 AM ET) next day</li>
                    <li><strong>Holding Period:</strong> Overnight (~17.5 hours)</li>
                    <li><strong>Trading Costs:</strong> 0.01% slippage (realistic for Alpaca commission-free trading)</li>
                    <li><strong>Initial Capital:</strong> ${config.INITIAL_CAPITAL:,.2f}</li>
                    <li><strong>Total Trades:</strong> {overnight_perf['total_trades'].iloc[0]:,}</li>
                </ul>
            </div>
        </div>

        <div class="section">
            <h2>🎯 Key Performance Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value {'positive' if overnight_perf['total_return'].iloc[0] > 0 else 'negative'}">
                        {overnight_perf['total_return'].iloc[0]:.1%}
                    </div>
                    <div class="metric-label">Total Return</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value {'positive' if overnight_perf['annualized_return'].iloc[0] > 0 else 'negative'}">
                        {overnight_perf['annualized_return'].iloc[0]:.1%}
                    </div>
                    <div class="metric-label">Annualized Return</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">
                        {overnight_perf['sharpe_ratio'].iloc[0]:.2f}
                    </div>
                    <div class="metric-label">Sharpe Ratio</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value {'positive' if overnight_perf['win_rate'].iloc[0] > 0.5 else 'negative'}">
                        {overnight_perf['win_rate'].iloc[0]:.1%}
                    </div>
                    <div class="metric-label">Win Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value negative">
                        {overnight_perf['max_drawdown'].iloc[0]:.1%}
                    </div>
                    <div class="metric-label">Maximum Drawdown</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">
                        ${overnight_perf['final_portfolio_value'].iloc[0]:,.2f}
                    </div>
                    <div class="metric-label">Final Portfolio Value</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📊 Strategy Comparison</h2>
            <p>Comparison of the overnight strategy against alternative approaches:</p>
            
            <table>
                <tr>
                    <th>Strategy</th>
                    <th>Total Return</th>
                    <th>Annualized Return</th>
                    <th>Sharpe Ratio</th>
                    <th>Max Drawdown</th>
                    <th>Total Trades</th>
                </tr>
    """
    
    # Add comparison table rows
    for _, row in comparison_df.iterrows():
        total_return = f"{row['Total Return']:.1%}" if pd.notna(row['Total Return']) else 'N/A'
        annual_return = f"{row['Annualized Return']:.1%}" if pd.notna(row['Annualized Return']) else 'N/A'
        sharpe = f"{row['Sharpe Ratio']:.2f}" if pd.notna(row['Sharpe Ratio']) and row['Sharpe Ratio'] != 'N/A' else 'N/A'
        max_dd = f"{row['Max Drawdown']:.1%}" if pd.notna(row['Max Drawdown']) and row['Max Drawdown'] != 'N/A' else 'N/A'
        
        # Color coding for best performance
        return_class = 'positive' if pd.notna(row['Total Return']) and row['Total Return'] > 0 else 'negative'
        
        html_content += f"""
                <tr>
                    <td><strong>{row['Strategy']}</strong></td>
                    <td class="{return_class}">{total_return}</td>
                    <td class="{return_class}">{annual_return}</td>
                    <td>{sharpe}</td>
                    <td>{max_dd}</td>
                    <td>{int(row['Total Trades']) if pd.notna(row['Total Trades']) else 'N/A'}</td>
                </tr>
        """
    
    html_content += """
            </table>
        </div>

        <div class="section">
            <h2>📈 Performance Analysis</h2>
            <div class="chart-container">
                <iframe src="charts/portfolio_performance.html" width="100%" height="800" frameborder="0"></iframe>
            </div>
        </div>

        <div class="section">
            <h2>📉 Risk Analysis</h2>
            <div class="chart-container">
                <iframe src="charts/drawdown_analysis.html" width="100%" height="400" frameborder="0"></iframe>
            </div>
        </div>

        <div class="section">
            <h2>🎲 Trade Distribution Analysis</h2>
            <div class="chart-container">
                <iframe src="charts/returns_distribution.html" width="100%" height="400" frameborder="0"></iframe>
            </div>
        </div>
    """
    
    # Add rolling metrics if available
    if os.path.exists('results/charts/rolling_metrics.html'):
        html_content += """
        <div class="section">
            <h2>📊 Rolling Performance Metrics</h2>
            <div class="chart-container">
                <iframe src="charts/rolling_metrics.html" width="100%" height="600" frameborder="0"></iframe>
            </div>
        </div>
        """
    
    # Monthly/Yearly breakdown
    trade_results = pd.read_csv('results/trade_results.csv')
    trade_results['sell_date'] = pd.to_datetime(trade_results['sell_date'])
    
    # Yearly performance
    yearly_performance = overnight_perf[['yearly_returns']].iloc[0].to_dict()
    yearly_data = eval(yearly_performance['yearly_returns'])  # Convert string dict to dict
    
    html_content += f"""
        <div class="section">
            <h2>📅 Yearly Performance Breakdown</h2>
            <table>
                <tr><th>Year</th><th>Return</th></tr>
    """
    
    for year, return_val in yearly_data.items():
        return_class = 'positive' if return_val > 0 else 'negative'
        html_content += f"""
                <tr>
                    <td>{year}</td>
                    <td class="{return_class}">{return_val:.1%}</td>
                </tr>
        """
    
    html_content += f"""
            </table>
        </div>

        <div class="section">
            <h2>💡 Key Insights</h2>
            <div class="highlight">
                <h3>Strategy Effectiveness</h3>
                <ul>
                    <li><strong>Overnight Edge:</strong> The strategy captures {overnight_perf['avg_return_per_trade'].iloc[0]*100:.3f}% average return per trade</li>
                    <li><strong>Risk-Adjusted Returns:</strong> Sharpe ratio of {overnight_perf['sharpe_ratio'].iloc[0]:.2f} indicates {'excellent' if overnight_perf['sharpe_ratio'].iloc[0] > 1.5 else 'good' if overnight_perf['sharpe_ratio'].iloc[0] > 1 else 'poor'} risk-adjusted performance</li>
                    <li><strong>Consistency:</strong> Win rate of {overnight_perf['win_rate'].iloc[0]:.1%} shows {'above-average' if overnight_perf['win_rate'].iloc[0] > 0.5 else 'below-average'} trade success</li>
                    <li><strong>Transaction Costs:</strong> Only {overnight_perf['gross_vs_net_impact'].iloc[0]*100:.2f}% cost per trade due to commission-free trading</li>
                </ul>
            </div>
        </div>

        <div class="conclusions">
            <h2>🏁 Conclusions & Recommendations</h2>
            
            <h3>✅ Strategy Strengths</h3>
            <ul>
                <li><strong>Strong Performance:</strong> {overnight_perf['annualized_return'].iloc[0]:.1%} annualized returns significantly outperform typical market returns</li>
                <li><strong>Cost Efficiency:</strong> Commission-free trading makes the strategy viable for retail investors</li>
                <li><strong>Systematic Approach:</strong> Clear rules for entry/exit make it suitable for automation</li>
                <li><strong>Bitcoin Exposure:</strong> Provides leveraged exposure to Bitcoin overnight moves</li>
            </ul>

            <h3>⚠️ Risk Considerations</h3>
            <ul>
                <li><strong>Volatility:</strong> {overnight_perf['volatility'].iloc[0]:.1%} annual volatility requires risk tolerance</li>
                <li><strong>Drawdowns:</strong> Maximum {overnight_perf['max_drawdown'].iloc[0]:.1%} drawdown could test investor patience</li>
                <li><strong>Market Dependency:</strong> Performance tied to Bitcoin/crypto market conditions</li>
                <li><strong>Strategy Decay:</strong> Overnight patterns may diminish as markets adapt</li>
            </ul>

            <h3>🚀 Implementation for Alpaca Trading</h3>
            <ul>
                <li><strong>Automation Ready:</strong> Strategy can be easily automated using Alpaca API</li>
                <li><strong>Cost Structure:</strong> Commission-free trading assumption is realistic for Alpaca</li>
                <li><strong>Position Sizing:</strong> Suitable for retail account sizes</li>
                <li><strong>Risk Management:</strong> Consider position sizing based on volatility conditions</li>
            </ul>

            <h3>🎯 Next Steps</h3>
            <ul>
                <li>Start with smaller position sizes to test live performance vs. backtest</li>
                <li>Monitor strategy performance and compare to these backtested expectations</li>
                <li>Consider implementing volatility-based position sizing</li>
                <li>Set up risk management rules (e.g., stop trading after significant drawdowns)</li>
            </ul>
        </div>

        <div class="section">
            <h2>📊 Technical Details</h2>
            <p><strong>Data Source:</strong> Yahoo Finance (IBIT daily OHLC data)</p>
            <p><strong>Analysis Period:</strong> {overnight_perf['start_date'].iloc[0]} to {overnight_perf['end_date'].iloc[0]} ({overnight_perf['years_traded'].iloc[0]:.2f} years)</p>
            <p><strong>Trading Days:</strong> {overnight_perf['days_traded'].iloc[0]:,.0f}</p>
            <p><strong>Cost Assumptions:</strong> 0.00% commission + 0.01% slippage</p>
            <p><strong>Methodology:</strong> Daily OHLC data using close-to-open returns</p>
        </div>

        <footer style="text-align: center; margin-top: 50px; color: #666;">
            <p>Report generated by IBIT Trading Strategy Analyzer</p>
            <p>This analysis is for educational purposes only and does not constitute financial advice.</p>
        </footer>
    </body>
    </html>
    """
    
    # Save HTML report
    with open('results/comprehensive_report.html', 'w') as f:
        f.write(html_content)
    
    print("✅ Comprehensive HTML report saved to results/comprehensive_report.html")
    print(f"📊 Total file size: {len(html_content):,} characters")
    return html_content


if __name__ == "__main__":
    report_html = create_html_report()
    print("🎉 Comprehensive report generation complete!")
    print("📁 Open 'results/comprehensive_report.html' in your browser to view the full report.")