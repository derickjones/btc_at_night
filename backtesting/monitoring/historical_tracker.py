"""
Historical Performance Tracker
Maintains long-term performance history and trend analysis for IBIT strategy.
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path
import seaborn as sns

class HistoricalTracker:
    """Tracks and analyzes long-term strategy performance trends."""
    
    def __init__(self):
        self.results_dir = Path('results/monthly_monitoring')
        self.history_file = self.results_dir / 'performance_history.csv'
        self.results_dir.mkdir(exist_ok=True)
        
    def update_history(self, monthly_report):
        """Add latest monthly results to historical tracking."""
        
        print("📚 Updating performance history...")
        
        # Extract key metrics for historical tracking
        new_record = {
            'date': monthly_report['report_date'],
            'period_days': monthly_report['analysis_period_days'],
            'annual_return': monthly_report['performance_analysis']['recent_metrics']['annual_return'],
            'sharpe_ratio': monthly_report['performance_analysis']['recent_metrics']['sharpe_ratio'],
            'win_rate': monthly_report['performance_analysis']['recent_metrics']['win_rate'],
            'max_drawdown': monthly_report['performance_analysis']['recent_metrics']['max_drawdown'],
            'total_trades': monthly_report['trade_summary']['total_trades'],
            'avg_return_per_trade': monthly_report['trade_summary']['average_return'],
            'best_trade': monthly_report['trade_summary']['best_trade'],
            'worst_trade': monthly_report['trade_summary']['worst_trade'],
            'return_vs_baseline': monthly_report['performance_analysis']['vs_baseline']['return_diff'],
            'sharpe_vs_baseline': monthly_report['performance_analysis']['vs_baseline']['sharpe_diff'],
            'performance_flags_count': len(monthly_report['performance_analysis']['performance_flags'])
        }
        
        # Load existing history or create new
        if self.history_file.exists():
            history_df = pd.read_csv(self.history_file)
            # Remove existing record for same date if exists
            history_df = history_df[history_df['date'] != new_record['date']]
        else:
            history_df = pd.DataFrame()
        
        # Add new record
        new_df = pd.DataFrame([new_record])
        history_df = pd.concat([history_df, new_df], ignore_index=True)
        
        # Sort by date
        history_df['date'] = pd.to_datetime(history_df['date'])
        history_df = history_df.sort_values('date')
        
        # Save updated history
        history_df.to_csv(self.history_file, index=False)
        
        print(f"✅ History updated: {len(history_df)} monthly records")
        
        return history_df
    
    def analyze_long_term_trends(self, min_periods=3):
        """Analyze long-term performance trends."""
        
        if not self.history_file.exists():
            print("⚠️  No historical data available for trend analysis")
            return None
        
        print(f"\n📈 Long-term Trend Analysis")
        print("=" * 35)
        
        df = pd.read_csv(self.history_file)
        df['date'] = pd.to_datetime(df['date'])
        
        if len(df) < min_periods:
            print(f"⚠️  Need at least {min_periods} periods for trend analysis (have {len(df)})")
            return None
        
        # Calculate trends
        recent_periods = min(6, len(df))  # Last 6 months or all available
        recent_data = df.tail(recent_periods)
        
        # Performance trends
        return_trend = np.polyfit(range(len(recent_data)), recent_data['annual_return'], 1)[0]
        sharpe_trend = np.polyfit(range(len(recent_data)), recent_data['sharpe_ratio'], 1)[0]
        winrate_trend = np.polyfit(range(len(recent_data)), recent_data['win_rate'], 1)[0]
        
        # Volatility of performance
        return_volatility = recent_data['annual_return'].std()
        performance_consistency = 1 / (1 + return_volatility)  # Higher = more consistent
        
        # Edge persistence analysis
        positive_months = (recent_data['return_vs_baseline'] > 0).sum()
        edge_persistence_rate = positive_months / len(recent_data)
        
        trend_analysis = {
            'periods_analyzed': len(recent_data),
            'total_history_months': len(df),
            'performance_trends': {
                'return_trend_monthly': return_trend,
                'sharpe_trend_monthly': sharpe_trend,
                'winrate_trend_monthly': winrate_trend
            },
            'stability_metrics': {
                'return_volatility': return_volatility,
                'performance_consistency': performance_consistency,
                'edge_persistence_rate': edge_persistence_rate
            },
            'recent_averages': {
                'avg_annual_return': recent_data['annual_return'].mean(),
                'avg_sharpe_ratio': recent_data['sharpe_ratio'].mean(),
                'avg_win_rate': recent_data['win_rate'].mean()
            }
        }
        
        # Print analysis
        print(f"Analysis Period: {recent_periods} months")
        print(f"Total History: {len(df)} monthly reports")
        
        print(f"\nTrends (per month):")
        print(f"  Return Trend: {return_trend:+.2%}")
        print(f"  Sharpe Trend: {sharpe_trend:+.3f}")
        print(f"  Win Rate Trend: {winrate_trend:+.2%}")
        
        print(f"\nStability:")
        print(f"  Performance Consistency: {performance_consistency:.2%}")
        print(f"  Edge Persistence Rate: {edge_persistence_rate:.1%} ({positive_months}/{len(recent_data)} months)")
        
        print(f"\nRecent Averages:")
        print(f"  Annual Return: {trend_analysis['recent_averages']['avg_annual_return']:.1%}")
        print(f"  Sharpe Ratio: {trend_analysis['recent_averages']['avg_sharpe_ratio']:.2f}")
        print(f"  Win Rate: {trend_analysis['recent_averages']['avg_win_rate']:.1%}")
        
        return trend_analysis
    
    def create_historical_dashboard(self):
        """Create comprehensive historical performance dashboard."""
        
        if not self.history_file.exists():
            print("⚠️  No historical data available for dashboard")
            return None
        
        print(f"\n📊 Creating historical dashboard...")
        
        df = pd.read_csv(self.history_file)
        df['date'] = pd.to_datetime(df['date'])
        
        # Create dashboard
        fig, axes = plt.subplots(3, 2, figsize=(16, 12))
        
        # 1. Annual Returns Over Time
        axes[0,0].plot(df['date'], df['annual_return'] * 100, 'b-o', linewidth=2, markersize=4)
        axes[0,0].axhline(y=72.3, color='red', linestyle='--', alpha=0.7, label='Original Baseline (72.3%)')
        axes[0,0].set_title('Annual Returns Trend')
        axes[0,0].set_ylabel('Annual Return (%)')
        axes[0,0].grid(True, alpha=0.3)
        axes[0,0].legend()
        
        # 2. Sharpe Ratio Over Time
        axes[0,1].plot(df['date'], df['sharpe_ratio'], 'g-o', linewidth=2, markersize=4)
        axes[0,1].axhline(y=1.81, color='red', linestyle='--', alpha=0.7, label='Original Baseline (1.81)')
        axes[0,1].set_title('Sharpe Ratio Trend')
        axes[0,1].set_ylabel('Sharpe Ratio')
        axes[0,1].grid(True, alpha=0.3)
        axes[0,1].legend()
        
        # 3. Win Rate Over Time
        axes[1,0].plot(df['date'], df['win_rate'] * 100, 'orange', marker='o', linewidth=2, markersize=4)
        axes[1,0].axhline(y=54.7, color='red', linestyle='--', alpha=0.7, label='Original Baseline (54.7%)')
        axes[1,0].set_title('Win Rate Trend')
        axes[1,0].set_ylabel('Win Rate (%)')
        axes[1,0].grid(True, alpha=0.3)
        axes[1,0].legend()
        
        # 4. Performance vs Baseline
        colors = ['red' if x < 0 else 'green' for x in df['return_vs_baseline']]
        axes[1,1].bar(range(len(df)), df['return_vs_baseline'] * 100, color=colors, alpha=0.7)
        axes[1,1].axhline(y=0, color='black', linewidth=1)
        axes[1,1].set_title('Performance vs Baseline')
        axes[1,1].set_ylabel('Return Difference (%)')
        axes[1,1].set_xlabel('Month')
        axes[1,1].grid(True, alpha=0.3)
        
        # 5. Trade Volume and Average Returns
        ax5 = axes[2,0]
        ax5_twin = ax5.twinx()
        
        bars = ax5.bar(range(len(df)), df['total_trades'], alpha=0.6, color='lightblue', label='Total Trades')
        line = ax5_twin.plot(range(len(df)), df['avg_return_per_trade'] * 100, 'ro-', 
                            linewidth=2, markersize=4, label='Avg Return per Trade')
        
        ax5.set_title('Trading Activity & Average Returns')
        ax5.set_ylabel('Total Trades', color='blue')
        ax5_twin.set_ylabel('Avg Return per Trade (%)', color='red')
        ax5.set_xlabel('Month')
        ax5.grid(True, alpha=0.3)
        
        # 6. Max Drawdown Tracking
        axes[2,1].plot(df['date'], df['max_drawdown'] * 100, 'purple', marker='o', linewidth=2, markersize=4)
        axes[2,1].axhline(y=-20.4, color='red', linestyle='--', alpha=0.7, label='Original Baseline (-20.4%)')
        axes[2,1].set_title('Maximum Drawdown Trend')
        axes[2,1].set_ylabel('Max Drawdown (%)')
        axes[2,1].grid(True, alpha=0.3)
        axes[2,1].legend()
        
        plt.tight_layout()
        
        # Save dashboard
        dashboard_file = self.results_dir / f'historical_dashboard_{datetime.now().strftime("%Y-%m-%d")}.png'
        plt.savefig(dashboard_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📈 Historical dashboard saved: {dashboard_file}")
        
        return str(dashboard_file)
    
    def generate_edge_persistence_report(self):
        """Generate detailed report on strategy edge persistence."""
        
        if not self.history_file.exists():
            return "No historical data available"
        
        df = pd.read_csv(self.history_file)
        df['date'] = pd.to_datetime(df['date'])
        
        # Edge persistence analysis
        edge_metrics = {
            'months_tracked': len(df),
            'months_above_baseline': (df['return_vs_baseline'] > 0).sum(),
            'months_significantly_above': (df['return_vs_baseline'] > 0.05).sum(),  # >5% above baseline
            'months_below_baseline': (df['return_vs_baseline'] < 0).sum(),
            'months_significantly_below': (df['return_vs_baseline'] < -0.05).sum(),  # >5% below baseline
            'average_outperformance': df['return_vs_baseline'].mean(),
            'best_month_outperformance': df['return_vs_baseline'].max(),
            'worst_month_outperformance': df['return_vs_baseline'].min(),
            'consistency_score': (df['return_vs_baseline'] > -0.02).mean()  # % of months within 2% of baseline
        }
        
        # Create summary report
        report = f"""
╔══════════════════════════════════════════════╗
║           EDGE PERSISTENCE ANALYSIS          ║
╚══════════════════════════════════════════════╝

📊 OVERALL ASSESSMENT:
   Months Tracked: {edge_metrics['months_tracked']}
   Edge Persistence Rate: {edge_metrics['months_above_baseline']}/{edge_metrics['months_tracked']} = {edge_metrics['months_above_baseline']/edge_metrics['months_tracked']:.1%}

📈 PERFORMANCE BREAKDOWN:
   Above Baseline: {edge_metrics['months_above_baseline']} months ({edge_metrics['months_above_baseline']/edge_metrics['months_tracked']:.1%})
   Significantly Above (>5%): {edge_metrics['months_significantly_above']} months
   Below Baseline: {edge_metrics['months_below_baseline']} months ({edge_metrics['months_below_baseline']/edge_metrics['months_tracked']:.1%})
   Significantly Below (<-5%): {edge_metrics['months_significantly_below']} months

🎯 PERFORMANCE METRICS:
   Average Outperformance: {edge_metrics['average_outperformance']:+.2%}
   Best Month: {edge_metrics['best_month_outperformance']:+.2%}
   Worst Month: {edge_metrics['worst_month_outperformance']:+.2%}
   Consistency Score: {edge_metrics['consistency_score']:.1%}

💡 INTERPRETATION:
"""
        
        # Add interpretation based on metrics
        if edge_metrics['months_above_baseline']/edge_metrics['months_tracked'] > 0.7:
            report += "   🟢 STRONG: Strategy edge appears persistent and reliable\n"
        elif edge_metrics['months_above_baseline']/edge_metrics['months_tracked'] > 0.5:
            report += "   🟡 MODERATE: Strategy shows edge but with some variability\n"
        else:
            report += "   🔴 WEAK: Strategy edge appears to be deteriorating\n"
        
        if edge_metrics['consistency_score'] > 0.8:
            report += "   🟢 HIGH CONSISTENCY: Performance stays close to baseline\n"
        elif edge_metrics['consistency_score'] > 0.6:
            report += "   🟡 MODERATE CONSISTENCY: Some performance volatility\n"
        else:
            report += "   🔴 LOW CONSISTENCY: High performance volatility\n"
        
        return report

def run_historical_analysis():
    """Run complete historical analysis."""
    
    tracker = HistoricalTracker()
    
    # Analyze trends
    trend_analysis = tracker.analyze_long_term_trends()
    
    # Create dashboard
    dashboard_file = tracker.create_historical_dashboard()
    
    # Generate edge persistence report
    edge_report = tracker.generate_edge_persistence_report()
    
    print(edge_report)
    
    return {
        'trend_analysis': trend_analysis,
        'dashboard_file': dashboard_file,
        'edge_report': edge_report
    }

if __name__ == "__main__":
    run_historical_analysis()