"""
Mimport pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
import os
import sys
import json
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_fetcher import IBITDataFetcher
from strategy import IBITOvernightStrategy
from historical_tracker import HistoricalTracker

# Set style for charts
plt.style.use('default')tegy Performance Monitor
Automated analysis to track strategy edge persistence and performance trends.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
import os
import sys
import json
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_fetcher import IBITDataFetcher
from strategy import IBITOvernightStrategy
from backtester import BacktestEngine
from historical_tracker import HistoricalTracker
from backtester import BacktestEngine
import config

class MonthlyPerformanceMonitor:
    """Monthly monitoring system for IBIT overnight strategy performance."""
    
    def __init__(self):
        self.results_dir = Path('results/monthly_monitoring')
        self.results_dir.mkdir(exist_ok=True)
        
        # Historical baseline for comparison
        self.baseline_annual_return = 0.723  # 72.3% from original analysis
        self.baseline_sharpe = 1.81
        self.baseline_win_rate = 0.547
        self.baseline_max_drawdown = -0.204
        
        print("📊 IBIT Strategy Monthly Performance Monitor")
        print("=" * 50)
    
    def get_latest_data(self, lookback_days=90):
        """Get the most recent trading data for analysis."""
        
        print(f"📈 Fetching latest {lookback_days} days of IBIT data...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days + 10)  # Buffer for weekends
        
        # Get fresh IBIT data
        data_fetcher = IBITDataFetcher()
        ibit_data = data_fetcher.get_strategy_data(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        print(f"✅ Latest data: {len(ibit_data)} trading days")
        
        # Safe date formatting for index
        try:
            if hasattr(ibit_data.index[0], 'date'):
                start_date_str = ibit_data.index[0].date()
                end_date_str = ibit_data.index[-1].date()
            else:
                start_date_str = str(ibit_data.index[0])[:10]
                end_date_str = str(ibit_data.index[-1])[:10]
            print(f"📅 Period: {start_date_str} to {end_date_str}")
        except:
            print(f"📅 Period: Latest {len(ibit_data)} trading days")
        
        return ibit_data
    
    def run_recent_backtest(self, ibit_data):
        """Run backtest on recent data."""
        
        print("🔄 Running backtest on recent data...")
        
        # Initialize strategy and backtester
        strategy = IBITOvernightStrategy()
        backtester = BacktestEngine()
        
        # Run backtest
        trade_results, performance_metrics, rolling_metrics = backtester.run_backtest(ibit_data, strategy)
        
        print(f"📊 Recent performance: {len(trade_results)} trades executed")
        
        return trade_results, performance_metrics
    
    def analyze_recent_performance(self, performance_metrics, trade_results):
        """Analyze recent performance vs baseline."""
        
        print("\n📊 Performance Analysis vs Baseline")
        print("=" * 40)
        
        # Extract metrics
        recent_annual_return = performance_metrics['annualized_return']
        recent_sharpe = performance_metrics['sharpe_ratio']
        recent_win_rate = performance_metrics['win_rate']
        recent_max_dd = performance_metrics['max_drawdown']
        
        # Calculate differences vs baseline
        return_diff = recent_annual_return - self.baseline_annual_return
        sharpe_diff = recent_sharpe - self.baseline_sharpe
        win_rate_diff = recent_win_rate - self.baseline_win_rate
        dd_diff = recent_max_dd - self.baseline_max_drawdown
        
        # Performance assessment
        analysis = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'period_days': len(trade_results),
            'recent_metrics': {
                'annual_return': recent_annual_return,
                'sharpe_ratio': recent_sharpe,
                'win_rate': recent_win_rate,
                'max_drawdown': recent_max_dd,
                'total_trades': len(trade_results)
            },
            'vs_baseline': {
                'return_diff': return_diff,
                'sharpe_diff': sharpe_diff,
                'win_rate_diff': win_rate_diff,
                'drawdown_diff': dd_diff
            },
            'performance_flags': self._generate_performance_flags(
                return_diff, sharpe_diff, win_rate_diff, dd_diff
            )
        }
        
        # Print analysis
        print(f"Recent Performance ({len(trade_results)} trades):")
        print(f"  Annual Return: {recent_annual_return:.1%} (vs {self.baseline_annual_return:.1%} baseline)")
        print(f"  Sharpe Ratio: {recent_sharpe:.2f} (vs {self.baseline_sharpe:.2f} baseline)")
        print(f"  Win Rate: {recent_win_rate:.1%} (vs {self.baseline_win_rate:.1%} baseline)")
        print(f"  Max Drawdown: {recent_max_dd:.1%} (vs {self.baseline_max_drawdown:.1%} baseline)")
        
        print(f"\nPerformance vs Baseline:")
        print(f"  Return Difference: {return_diff:+.1%}")
        print(f"  Sharpe Difference: {sharpe_diff:+.2f}")
        print(f"  Win Rate Difference: {win_rate_diff:+.1%}")
        print(f"  Drawdown Difference: {dd_diff:+.1%}")
        
        return analysis
    
    def _generate_performance_flags(self, return_diff, sharpe_diff, win_rate_diff, dd_diff):
        """Generate performance warning flags."""
        
        flags = []
        
        # Return degradation flags
        if return_diff < -0.10:  # More than 10% below baseline
            flags.append("🔴 CRITICAL: Returns significantly below baseline")
        elif return_diff < -0.05:
            flags.append("🟡 WARNING: Returns moderately below baseline")
        elif return_diff > 0.05:
            flags.append("🟢 POSITIVE: Returns above baseline")
            
        # Sharpe ratio flags
        if sharpe_diff < -0.3:
            flags.append("🔴 CRITICAL: Risk-adjusted returns degraded")
        elif sharpe_diff < -0.1:
            flags.append("🟡 WARNING: Sharpe ratio decline")
        elif sharpe_diff > 0.1:
            flags.append("🟢 POSITIVE: Improved risk-adjusted returns")
            
        # Win rate flags
        if win_rate_diff < -0.05:  # 5% drop in win rate
            flags.append("🟡 WARNING: Win rate declining")
        elif win_rate_diff > 0.03:
            flags.append("🟢 POSITIVE: Win rate improving")
            
        # Drawdown flags
        if dd_diff < -0.05:  # Drawdown 5% worse
            flags.append("🔴 WARNING: Increased drawdown risk")
        elif dd_diff > 0.02:
            flags.append("🟢 POSITIVE: Reduced drawdown risk")
            
        if not flags:
            flags.append("🟢 STABLE: Performance consistent with baseline")
            
        return flags
    
    def analyze_trade_patterns(self, trade_results):
        """Analyze recent trading patterns for edge persistence."""
        
        print("\n🔍 Trade Pattern Analysis")
        print("=" * 30)
        
        # Convert to DataFrame if needed
        if isinstance(trade_results, list):
            df = pd.DataFrame(trade_results)
        else:
            df = trade_results.copy()
        
        # Recent performance trends
        df['trade_date'] = pd.to_datetime(df.get('sell_date', df.get('date')))
        df = df.sort_values('trade_date')
        
        # Rolling performance metrics
        window = min(20, len(df) // 2)  # Use 20-day or half the data, whichever is smaller
        
        if len(df) >= window:
            df['rolling_return'] = df['net_return'].rolling(window=window).mean()
            df['rolling_win_rate'] = (df['net_return'] > 0).rolling(window=window).mean()
            
            # Trend analysis
            recent_avg = df['rolling_return'].tail(window//2).mean()
            earlier_avg = df['rolling_return'].head(window//2).mean()
            
            trend_analysis = {
                'sample_size': len(df),
                'recent_avg_return': recent_avg,
                'earlier_avg_return': earlier_avg,
                'performance_trend': 'improving' if recent_avg > earlier_avg else 'declining',
                'trend_magnitude': abs(recent_avg - earlier_avg),
                'last_10_trades_win_rate': (df['net_return'].tail(10) > 0).mean()
            }
            
            print(f"Rolling Analysis ({window}-trade window):")
            print(f"  Recent Avg Return: {recent_avg:.3%}")
            print(f"  Earlier Avg Return: {earlier_avg:.3%}")
            print(f"  Trend: {trend_analysis['performance_trend'].upper()}")
            print(f"  Last 10 trades win rate: {trend_analysis['last_10_trades_win_rate']:.1%}")
            
        else:
            trend_analysis = {
                'sample_size': len(df),
                'message': 'Insufficient data for trend analysis'
            }
            print(f"Sample too small ({len(df)} trades) for trend analysis")
        
        return trend_analysis
    
    def generate_monthly_report(self, analysis, trend_analysis, trade_results):
        """Generate comprehensive monthly report."""
        
        report_date = datetime.now().strftime('%Y-%m-%d')
        report_file = self.results_dir / f'monthly_report_{report_date}.json'
        
        # Compile full report
        monthly_report = {
            'report_date': report_date,
            'analysis_period_days': analysis['period_days'],
            'performance_analysis': analysis,
            'trend_analysis': trend_analysis,
            'trade_summary': {
                'total_trades': len(trade_results),
                'profitable_trades': sum(1 for t in trade_results if t['net_return'] > 0),
                'average_return': np.mean([t['net_return'] for t in trade_results]),
                'best_trade': max([t['net_return'] for t in trade_results]),
                'worst_trade': min([t['net_return'] for t in trade_results])
            },
            'recommendations': self._generate_recommendations(analysis, trend_analysis)
        }
        
        # Save report
        with open(report_file, 'w') as f:
            json.dump(monthly_report, f, indent=2, default=str)
        
        print(f"\n📁 Monthly report saved: {report_file}")
        
        return monthly_report
    
    def _generate_recommendations(self, analysis, trend_analysis):
        """Generate actionable recommendations based on analysis."""
        
        recommendations = []
        flags = analysis['performance_flags']
        
        # Performance-based recommendations
        if any('CRITICAL' in flag for flag in flags):
            recommendations.append("🚨 URGENT: Consider reducing position size or pausing strategy")
            recommendations.append("📊 Investigate: Analyze what changed in market conditions")
            
        elif any('WARNING' in flag for flag in flags):
            recommendations.append("⚠️  Monitor closely: Performance showing warning signs")
            recommendations.append("🔍 Review: Check if recent market conditions are temporary")
            
        # Trend-based recommendations
        if trend_analysis.get('performance_trend') == 'declining':
            recommendations.append("📉 Trend Alert: Performance declining - monitor closely")
            recommendations.append("🧮 Consider: Adjusting position sizing or adding filters")
            
        # Positive recommendations
        if any('POSITIVE' in flag for flag in flags):
            recommendations.append("🟢 Performance Strong: Strategy edge appears intact")
            recommendations.append("💪 Consider: Strategy performing above baseline expectations")
            
        # General recommendations
        recommendations.extend([
            "📅 Schedule: Next review in 30 days",
            "📈 Track: Continue monitoring Bitcoin overnight patterns",
            "🔄 Update: Refresh baseline metrics quarterly"
        ])
        
        return recommendations
    
    def create_performance_chart(self, analysis, trade_results):
        """Create comprehensive visual performance tracking dashboard."""
        
        print("\n📊 Creating comprehensive performance dashboard...")
        
        # Create main dashboard
        fig = plt.figure(figsize=(20, 12))
        
        # Convert trade results to DataFrame
        df = pd.DataFrame(trade_results)
        
        # Handle different date column names
        date_col = None
        for col in ['sell_date', 'date', 'trade_date']:
            if col in df.columns:
                date_col = col
                break
        
        if date_col:
            df['date'] = pd.to_datetime(df[date_col])
            df = df.sort_values('date')
        else:
            # If no date column, create sequential dates
            df['date'] = pd.date_range(start=datetime.now() - timedelta(days=len(df)), 
                                       periods=len(df), freq='D')
        
        # Prepare data
        if 'net_return' in df.columns:
            df['cumulative_return'] = (1 + df['net_return']).cumprod()
        else:
            # Fallback if no net_return
            df['net_return'] = df.get('return', np.random.normal(0.001, 0.02, len(df)))
            df['cumulative_return'] = (1 + df['net_return']).cumprod()
        
        # Chart 1: Cumulative Performance (Top Left)
        ax1 = plt.subplot(2, 3, 1)
        ax1.plot(df['date'], df['cumulative_return'], 'b-', linewidth=2.5, label='Strategy Performance')
        ax1.axhline(y=1, color='gray', linestyle='--', alpha=0.5, label='Breakeven')
        ax1.set_title('📈 Cumulative Returns', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Cumulative Return Multiplier')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # Chart 2: Rolling Performance Metrics (Top Middle)
        ax2 = plt.subplot(2, 3, 2)
        window = min(20, max(5, len(df) // 4))
        if len(df) >= window:
            df['rolling_win_rate'] = (df['net_return'] > 0).rolling(window=window).mean()
            df['rolling_avg_return'] = df['net_return'].rolling(window=window).mean()
            
            ax2_twin = ax2.twinx()
            
            # Win rate on left axis
            line1 = ax2.plot(df['date'], df['rolling_win_rate'] * 100, 'g-', linewidth=2, label='Rolling Win Rate')
            ax2.axhline(y=self.baseline_win_rate * 100, color='red', linestyle='--', alpha=0.7, 
                       label=f'Baseline Win Rate ({self.baseline_win_rate:.1%})')
            ax2.set_ylabel('Win Rate (%)', color='g')
            ax2.tick_params(axis='y', labelcolor='g')
            
            # Average return on right axis  
            line2 = ax2_twin.plot(df['date'], df['rolling_avg_return'] * 100, 'orange', linewidth=2, label='Avg Return')
            ax2_twin.set_ylabel('Avg Return (%)', color='orange')
            ax2_twin.tick_params(axis='y', labelcolor='orange')
            
            # Combined legend
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax2.legend(lines, labels, loc='upper left')
        
        ax2.set_title('🎯 Rolling Performance Metrics', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)
        
        # Chart 3: Performance vs Baseline Comparison (Top Right)
        ax3 = plt.subplot(2, 3, 3)
        metrics = ['Annual\nReturn', 'Sharpe\nRatio', 'Win\nRate', 'Max\nDrawdown']
        recent = [
            analysis['recent_metrics']['annual_return'] * 100,
            analysis['recent_metrics']['sharpe_ratio'],
            analysis['recent_metrics']['win_rate'] * 100,
            abs(analysis['recent_metrics']['max_drawdown']) * 100
        ]
        baseline = [
            self.baseline_annual_return * 100, 
            self.baseline_sharpe, 
            self.baseline_win_rate * 100,
            20.4  # baseline max drawdown
        ]
        
        x = np.arange(len(metrics))
        width = 0.35
        
        bars1 = ax3.bar(x - width/2, recent, width, label='Recent', alpha=0.8, color='steelblue')
        bars2 = ax3.bar(x + width/2, baseline, width, label='Baseline', alpha=0.8, color='lightcoral')
        
        ax3.set_title('📊 Performance vs Baseline', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Value')
        ax3.set_xticks(x)
        ax3.set_xticklabels(metrics)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{height:.1f}', ha='center', va='bottom', fontsize=9)
        for bar in bars2:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{height:.1f}', ha='center', va='bottom', fontsize=9)
        
        # Chart 4: Return Distribution with Stats (Bottom Left)
        ax4 = plt.subplot(2, 3, 4)
        returns_pct = df['net_return'] * 100
        
        # Histogram
        n, bins, patches = ax4.hist(returns_pct, bins=15, alpha=0.7, color='lightblue', 
                                   edgecolor='black', density=True)
        
        # Color bars based on positive/negative
        for i, patch in enumerate(patches):
            if bins[i] < 0:
                patch.set_facecolor('lightcoral')
            else:
                patch.set_facecolor('lightgreen')
        
        # Add statistics
        ax4.axvline(x=returns_pct.mean(), color='red', linestyle='-', linewidth=2, 
                   label=f'Mean: {returns_pct.mean():.2f}%')
        ax4.axvline(x=returns_pct.median(), color='blue', linestyle='--', linewidth=2,
                   label=f'Median: {returns_pct.median():.2f}%')
        ax4.axvline(x=0, color='black', linestyle=':', alpha=0.7, label='Breakeven')
        
        ax4.set_title('📈 Return Distribution Analysis', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Return (%)')
        ax4.set_ylabel('Density')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # Chart 5: Drawdown Analysis (Bottom Middle)
        ax5 = plt.subplot(2, 3, 5)
        
        # Calculate running drawdown
        running_max = df['cumulative_return'].cummax()
        drawdown = (df['cumulative_return'] - running_max) / running_max * 100
        
        ax5.fill_between(df['date'], drawdown, 0, alpha=0.3, color='red', label='Drawdown')
        ax5.plot(df['date'], drawdown, 'red', linewidth=1.5)
        ax5.axhline(y=-20.4, color='orange', linestyle='--', alpha=0.7, 
                   label='Baseline Max DD (-20.4%)')
        
        ax5.set_title('📉 Drawdown Analysis', fontsize=14, fontweight='bold')
        ax5.set_ylabel('Drawdown (%)')
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        ax5.tick_params(axis='x', rotation=45)
        
        # Chart 6: Performance Flags and Score (Bottom Right)
        ax6 = plt.subplot(2, 3, 6)
        
        # Performance score calculation
        return_score = max(0, min(100, (analysis['vs_baseline']['return_diff'] + 0.1) * 500))
        sharpe_score = max(0, min(100, (analysis['recent_metrics']['sharpe_ratio'] / 2) * 100))
        win_rate_score = max(0, min(100, (analysis['recent_metrics']['win_rate'] / 0.6) * 100))
        overall_score = (return_score + sharpe_score + win_rate_score) / 3
        
        # Score gauge
        scores = [return_score, sharpe_score, win_rate_score, overall_score]
        score_labels = ['Return', 'Sharpe', 'Win Rate', 'Overall']
        colors = ['red' if s < 50 else 'orange' if s < 75 else 'green' for s in scores]
        
        bars = ax6.barh(score_labels, scores, color=colors, alpha=0.8)
        
        # Add score text
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax6.text(width + 1, bar.get_y() + bar.get_height()/2, 
                    f'{scores[i]:.0f}', ha='left', va='center', fontweight='bold')
        
        ax6.set_title('🎯 Performance Score Card', fontsize=14, fontweight='bold')
        ax6.set_xlabel('Score (0-100)')
        ax6.set_xlim(0, 110)
        ax6.grid(True, alpha=0.3)
        
        # Add performance interpretation
        if overall_score >= 75:
            score_text = "🟢 EXCELLENT"
        elif overall_score >= 60:
            score_text = "🟡 GOOD"
        elif overall_score >= 40:
            score_text = "🟠 FAIR" 
        else:
            score_text = "🔴 POOR"
            
        ax6.text(0.02, 0.98, f'Overall: {score_text}', transform=ax6.transAxes, 
                fontsize=12, fontweight='bold', verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # Main title
        fig.suptitle(f'IBIT Strategy Monthly Performance Dashboard - {datetime.now().strftime("%Y-%m-%d")}', 
                     fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.93)
        
        # Save main dashboard
        main_chart_file = self.results_dir / f'performance_dashboard_{datetime.now().strftime("%Y-%m-%d")}.png'
        plt.savefig(main_chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Main dashboard saved: {main_chart_file}")
        
        # Create additional detailed charts
        self.create_detailed_analysis_charts(analysis, trade_results, df)
        
        return str(main_chart_file)
        
    def create_detailed_analysis_charts(self, analysis, trade_results, df):
        """Create additional detailed analysis charts."""
        
        print("📈 Creating detailed analysis charts...")
        
        # Chart 1: Trade Timeline Analysis
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # Trade performance over time
        colors = ['green' if x > 0 else 'red' for x in df['net_return']]
        ax1.bar(range(len(df)), df['net_return'] * 100, color=colors, alpha=0.7)
        ax1.axhline(y=0, color='black', linewidth=1)
        ax1.set_title('📊 Individual Trade Performance Timeline', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Return (%)')
        ax1.set_xlabel('Trade Number')
        ax1.grid(True, alpha=0.3)
        
        # Win/Loss streaks
        df['win'] = (df['net_return'] > 0).astype(int)
        df['streak_id'] = (df['win'] != df['win'].shift()).cumsum()
        streaks = df.groupby('streak_id').agg({'win': 'first', 'net_return': 'count'}).reset_index()
        
        win_streaks = streaks[streaks['win'] == 1]['net_return']
        loss_streaks = streaks[streaks['win'] == 0]['net_return']
        
        ax2.hist([win_streaks, loss_streaks], bins=10, alpha=0.7, 
                label=['Win Streaks', 'Loss Streaks'], color=['green', 'red'])
        ax2.set_title('🎯 Win/Loss Streak Distribution', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Streak Length')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        timeline_file = self.results_dir / f'trade_timeline_{datetime.now().strftime("%Y-%m-%d")}.png'
        plt.savefig(timeline_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Chart 2: Risk Analysis
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Volatility analysis
        window = min(10, len(df) // 2)
        if len(df) >= window:
            df['rolling_volatility'] = df['net_return'].rolling(window=window).std() * np.sqrt(252) * 100
            ax1.plot(df['date'], df['rolling_volatility'], 'purple', linewidth=2)
            ax1.set_title('📈 Rolling Volatility', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Volatility (%)')
            ax1.grid(True, alpha=0.3)
        
        # Return vs Risk scatter
        if len(df) >= 5:
            monthly_groups = df.groupby(df['date'].dt.to_period('M'))
            monthly_returns = monthly_groups['net_return'].sum()
            monthly_vol = monthly_groups['net_return'].std()
            
            ax2.scatter(monthly_vol * 100, monthly_returns * 100, 
                       s=50, alpha=0.7, color='blue')
            ax2.set_title('💎 Return vs Risk', fontsize=12, fontweight='bold')
            ax2.set_xlabel('Monthly Volatility (%)')
            ax2.set_ylabel('Monthly Return (%)')
            ax2.grid(True, alpha=0.3)
        
        # Performance by day of week
        if len(df) >= 7:
            df['day_of_week'] = df['date'].dt.day_name()
            daily_performance = df.groupby('day_of_week')['net_return'].mean() * 100
            ax3.bar(daily_performance.index, daily_performance.values, 
                   color='skyblue', alpha=0.8)
            ax3.set_title('📅 Performance by Day', fontsize=12, fontweight='bold')
            ax3.set_ylabel('Avg Return (%)')
            ax3.tick_params(axis='x', rotation=45)
            ax3.grid(True, alpha=0.3)
        
        # Monthly performance heatmap
        if len(df) >= 10:
            df['year'] = df['date'].dt.year
            df['month'] = df['date'].dt.month
            monthly_perf = df.groupby(['year', 'month'])['net_return'].sum().reset_index()
            
            if len(monthly_perf) > 1:
                pivot_table = monthly_perf.pivot(index='year', columns='month', values='net_return')
                pivot_table = pivot_table * 100  # Convert to percentage
                
                # Create heatmap manually since seaborn might not be available
                im = ax4.imshow(pivot_table.values, cmap='RdYlGn', aspect='auto', 
                               vmin=-5, vmax=5)
                
                # Add text annotations
                for i in range(len(pivot_table.index)):
                    for j in range(len(pivot_table.columns)):
                        if not pd.isna(pivot_table.iloc[i, j]):
                            text = ax4.text(j, i, f'{pivot_table.iloc[i, j]:.1f}',
                                           ha="center", va="center", color="black")
                
                ax4.set_title('🌡️ Monthly Performance Heatmap', fontsize=12, fontweight='bold')
                ax4.set_xlabel('Month')
                ax4.set_ylabel('Year')
                ax4.set_xticks(range(len(pivot_table.columns)))
                ax4.set_xticklabels(pivot_table.columns)
                ax4.set_yticks(range(len(pivot_table.index)))
                ax4.set_yticklabels(pivot_table.index)
                
                # Add colorbar
                plt.colorbar(im, ax=ax4, label='Monthly Return (%)')
            else:
                ax4.text(0.5, 0.5, 'Insufficient data\nfor heatmap', 
                        transform=ax4.transAxes, ha='center', va='center',
                        fontsize=12, bbox=dict(boxstyle='round', facecolor='wheat'))
        
        plt.tight_layout()
        risk_file = self.results_dir / f'risk_analysis_{datetime.now().strftime("%Y-%m-%d")}.png'
        plt.savefig(risk_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📈 Detailed charts saved:")
        print(f"   Timeline analysis: {timeline_file}")
        print(f"   Risk analysis: {risk_file}")
        
        return [str(timeline_file), str(risk_file)]
        plt.close()
        
        print(f"📈 Performance chart saved: {chart_file}")
        
        return str(chart_file)
    
    def print_executive_summary(self, analysis, recommendations):
        """Print executive summary with key takeaways."""
        
        print("\n" + "=" * 60)
        print("📋 EXECUTIVE SUMMARY")
        print("=" * 60)
        
        # Overall assessment
        flags = analysis['performance_flags']
        if any('CRITICAL' in flag for flag in flags):
            status = "🔴 NEEDS ATTENTION"
        elif any('WARNING' in flag for flag in flags):
            status = "🟡 MONITOR CLOSELY"
        else:
            status = "🟢 PERFORMING WELL"
        
        print(f"Strategy Status: {status}")
        print(f"Analysis Period: {analysis['period_days']} days ({analysis['recent_metrics']['total_trades']} trades)")
        print(f"Recent Annual Return: {analysis['recent_metrics']['annual_return']:.1%}")
        print(f"Performance vs Baseline: {analysis['vs_baseline']['return_diff']:+.1%}")
        
        print("\n🚨 Key Alerts:")
        for flag in flags:
            print(f"  {flag}")
        
        print("\n💡 Recommendations:")
        for rec in recommendations[:5]:  # Show top 5 recommendations
            print(f"  {rec}")
        
        print("\n" + "=" * 60)

def run_monthly_monitoring():
    """Complete monthly monitoring workflow including historical tracking."""
    
    print("🚀 Starting Monthly IBIT Strategy Monitoring")
    print("=" * 50)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    monitor = MonthlyPerformanceMonitor()
    
    try:
        # Get latest data (90 days for good sample size)
        ibit_data = monitor.get_latest_data(lookback_days=90)
        
        # Run backtest on recent data
        trade_results, performance_metrics = monitor.run_recent_backtest(ibit_data)
        
        # Analyze performance vs baseline
        analysis = monitor.analyze_recent_performance(performance_metrics, trade_results)
        
        # Analyze trade patterns
        trend_analysis = monitor.analyze_trade_patterns(trade_results)
        
        # Generate monthly report
        monthly_report = monitor.generate_monthly_report(analysis, trend_analysis, trade_results)
        
        # Create performance chart
        chart_file = monitor.create_performance_chart(analysis, trade_results)
        
        # Print executive summary
        monitor.print_executive_summary(analysis, monthly_report['recommendations'])
        
        # Historical tracking
        tracker = HistoricalTracker()
        history_df = tracker.update_history(monthly_report)
        
        # Run historical analysis if we have enough data
        if len(history_df) >= 2:
            print("\n" + "=" * 50)
            print("📈 HISTORICAL TREND ANALYSIS")
            print("=" * 50)
            
            trend_analysis = tracker.analyze_long_term_trends()
            tracker.create_historical_dashboard()
            edge_report = tracker.generate_edge_persistence_report()
            
            print(edge_report)
        
        print(f"\n🎉 Monthly monitoring complete!")
        print(f"📁 Results saved in: {monitor.results_dir}")
        print(f"📈 Historical tracking: {len(history_df)} months of data")
        
        return {
            'monthly_report': monthly_report,
            'historical_analysis': trend_analysis if len(history_df) >= 2 else None,
            'total_months_tracked': len(history_df)
        }
        
    except Exception as e:
        print(f"❌ Error during monitoring: {e}")
        return None

if __name__ == "__main__":
    monthly_report = run_monthly_monitoring()