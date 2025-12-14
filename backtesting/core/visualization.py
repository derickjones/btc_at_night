"""
Visualization module for IBIT overnight trading strategy analysis.
Creates comprehensive charts and performance graphs.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime
import os

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class StrategyVisualizer:
    """Create comprehensive visualizations for strategy analysis."""
    
    def __init__(self, results_dir="results"):
        self.results_dir = results_dir
        
    def load_data(self):
        """Load all result data."""
        trade_results = pd.read_csv(f'{self.results_dir}/trade_results.csv')
        trade_results['buy_date'] = pd.to_datetime(trade_results['buy_date'])
        trade_results['sell_date'] = pd.to_datetime(trade_results['sell_date'])
        
        performance = pd.read_csv(f'{self.results_dir}/performance_summary.csv')
        
        try:
            rolling_metrics = pd.read_csv(f'{self.results_dir}/rolling_metrics.csv')
        except FileNotFoundError:
            rolling_metrics = pd.DataFrame()
            
        return trade_results, performance, rolling_metrics
    
    def create_portfolio_performance_chart(self, trade_results):
        """Create portfolio value over time chart."""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Portfolio Value Over Time', 'Monthly Returns'),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )
        
        # Portfolio value over time
        fig.add_trace(
            go.Scatter(
                x=trade_results['sell_date'],
                y=trade_results['portfolio_value'],
                mode='lines',
                name='Portfolio Value',
                line=dict(color='blue', width=2)
            ),
            row=1, col=1
        )
        
        # Add initial capital line
        fig.add_hline(
            y=10000,
            line_dash="dash",
            line_color="gray",
            annotation_text="Initial Capital ($10,000)",
            row=1, col=1
        )
        
        # Monthly returns
        trade_results_monthly = trade_results.copy()
        trade_results_monthly['year_month'] = trade_results_monthly['sell_date'].dt.to_period('M')
        monthly_returns = trade_results_monthly.groupby('year_month')['net_return'].sum()
        
        colors = ['green' if x > 0 else 'red' for x in monthly_returns]
        
        fig.add_trace(
            go.Bar(
                x=[str(x) for x in monthly_returns.index],
                y=monthly_returns.values * 100,
                name='Monthly Returns (%)',
                marker_color=colors
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title='IBIT Overnight Strategy - Portfolio Performance',
            height=800,
            showlegend=True
        )
        
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Portfolio Value ($)", row=1, col=1)
        fig.update_yaxes(title_text="Return (%)", row=2, col=1)
        
        return fig
    
    def create_drawdown_chart(self, trade_results):
        """Create drawdown analysis chart."""
        portfolio_values = trade_results['portfolio_value']
        running_max = portfolio_values.expanding().max()
        drawdowns = (portfolio_values - running_max) / running_max * 100
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=trade_results['sell_date'],
                y=drawdowns,
                mode='lines',
                fill='tonexty',
                name='Drawdown %',
                line=dict(color='red'),
                fillcolor='rgba(255,0,0,0.3)'
            )
        )
        
        fig.add_hline(y=0, line_color="black", line_width=1)
        
        fig.update_layout(
            title='Portfolio Drawdown Analysis',
            xaxis_title='Date',
            yaxis_title='Drawdown (%)',
            height=400
        )
        
        return fig
    
    def create_returns_distribution(self, trade_results):
        """Create returns distribution chart."""
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Trade Returns Distribution', 'Returns vs Trade Number'),
        )
        
        # Histogram of returns
        fig.add_trace(
            go.Histogram(
                x=trade_results['net_return'] * 100,
                nbinsx=50,
                name='Returns Distribution',
                opacity=0.7
            ),
            row=1, col=1
        )
        
        # Returns over time (scatter)
        colors = ['green' if x > 0 else 'red' for x in trade_results['net_return']]
        
        fig.add_trace(
            go.Scatter(
                x=list(range(len(trade_results))),
                y=trade_results['net_return'] * 100,
                mode='markers',
                marker=dict(color=colors, size=4),
                name='Individual Trades'
            ),
            row=1, col=2
        )
        
        fig.add_hline(y=0, line_color="black", line_width=1, row=1, col=2)
        
        fig.update_layout(
            title='Trade Returns Analysis',
            height=400,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Return (%)", row=1, col=1)
        fig.update_xaxes(title_text="Trade Number", row=1, col=2)
        fig.update_yaxes(title_text="Frequency", row=1, col=1)
        fig.update_yaxes(title_text="Return (%)", row=1, col=2)
        
        return fig
    
    def create_rolling_metrics_chart(self, rolling_metrics):
        """Create rolling performance metrics chart."""
        if rolling_metrics.empty:
            return None
            
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Rolling Win Rate', 'Rolling Avg Return', 
                          'Rolling Sharpe Ratio', 'Rolling Max Drawdown'),
            vertical_spacing=0.1
        )
        
        # Rolling win rate
        fig.add_trace(
            go.Scatter(
                x=rolling_metrics['trade_number'],
                y=rolling_metrics['rolling_win_rate'] * 100,
                mode='lines',
                name='Win Rate %',
                line=dict(color='blue')
            ),
            row=1, col=1
        )
        
        # Rolling average return
        fig.add_trace(
            go.Scatter(
                x=rolling_metrics['trade_number'],
                y=rolling_metrics['rolling_avg_return'] * 100,
                mode='lines',
                name='Avg Return %',
                line=dict(color='green')
            ),
            row=1, col=2
        )
        
        # Rolling Sharpe ratio
        fig.add_trace(
            go.Scatter(
                x=rolling_metrics['trade_number'],
                y=rolling_metrics['rolling_sharpe'],
                mode='lines',
                name='Sharpe Ratio',
                line=dict(color='purple')
            ),
            row=2, col=1
        )
        
        # Rolling max drawdown
        fig.add_trace(
            go.Scatter(
                x=rolling_metrics['trade_number'],
                y=rolling_metrics['rolling_max_drawdown'] * 100,
                mode='lines',
                name='Max Drawdown %',
                line=dict(color='red')
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title='Rolling Performance Metrics (30-Trade Windows)',
            height=600,
            showlegend=False
        )
        
        return fig
    
    def create_strategy_comparison_chart(self, overnight_results, day_results, continuous_results):
        """Create strategy comparison chart."""
        
        # Calculate cumulative returns for each strategy
        strategies = {
            'Overnight Only': overnight_results,
            'Day Only': day_results, 
            'Buy & Hold': continuous_results
        }
        
        fig = go.Figure()
        
        colors = ['blue', 'red', 'green']
        
        for i, (strategy_name, results) in enumerate(strategies.items()):
            if isinstance(results, dict):  # Single value (buy & hold)
                # Create a line for buy & hold
                dates = overnight_results['sell_date']
                initial_value = 10000
                final_value = initial_value * (1 + results['total_return'])
                buy_hold_values = np.linspace(initial_value, final_value, len(dates))
                
                fig.add_trace(
                    go.Scatter(
                        x=dates,
                        y=buy_hold_values,
                        mode='lines',
                        name=strategy_name,
                        line=dict(color=colors[i], width=2)
                    )
                )
            else:
                fig.add_trace(
                    go.Scatter(
                        x=results['sell_date'],
                        y=results['portfolio_value'],
                        mode='lines',
                        name=strategy_name,
                        line=dict(color=colors[i], width=2)
                    )
                )
        
        fig.update_layout(
            title='Strategy Comparison: Overnight vs Day vs Buy & Hold',
            xaxis_title='Date',
            yaxis_title='Portfolio Value ($)',
            height=500,
            legend=dict(x=0.02, y=0.98)
        )
        
        return fig
    
    def save_charts(self, charts, output_dir="results/charts"):
        """Save all charts to HTML files."""
        os.makedirs(output_dir, exist_ok=True)
        
        for name, chart in charts.items():
            if chart is not None:
                chart.write_html(f"{output_dir}/{name}.html")
                print(f"✅ Saved {name}.html")
    
    def create_all_visualizations(self):
        """Create all visualization charts."""
        print("📊 Creating comprehensive visualizations...")
        
        # Load data
        trade_results, performance, rolling_metrics = self.load_data()
        
        charts = {}
        
        # Portfolio performance
        charts['portfolio_performance'] = self.create_portfolio_performance_chart(trade_results)
        
        # Drawdown analysis
        charts['drawdown_analysis'] = self.create_drawdown_chart(trade_results)
        
        # Returns analysis
        charts['returns_distribution'] = self.create_returns_distribution(trade_results)
        
        # Rolling metrics
        if not rolling_metrics.empty:
            charts['rolling_metrics'] = self.create_rolling_metrics_chart(rolling_metrics)
        
        # Save charts
        self.save_charts(charts)
        
        return charts


if __name__ == "__main__":
    # Create all visualizations
    visualizer = StrategyVisualizer()
    charts = visualizer.create_all_visualizations()
    print("🎉 All visualizations created successfully!")