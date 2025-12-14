"""
Comprehensive IBIT overnight strategy analysis.
Fetches all available data and runs complete backtesting analysis.
"""

import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_fetcher import IBITDataFetcher
from strategy import IBITOvernightStrategy
from backtester import BacktestEngine
import config


def run_comprehensive_analysis():
    """Run comprehensive analysis on all available IBIT data."""
    
    print("🚀 Starting Comprehensive IBIT Overnight Strategy Analysis")
    print("=" * 80)
    
    # Initialize components
    data_fetcher = IBITDataFetcher()
    strategy = IBITOvernightStrategy()
    backtester = BacktestEngine()
    
    # Use all available data from IBIT launch to present
    start_date = config.START_DATE  # IBIT launched on 2021-10-19
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"📅 Analysis Period: {start_date} to {end_date}")
    print(f"💰 Initial Capital: ${config.INITIAL_CAPITAL:,.2f}")
    print(f"💸 Transaction Cost: {config.TRANSACTION_COST:.1%} per trade")
    print(f"⚡ Slippage: {config.SLIPPAGE:.2%} per trade")
    print()
    
    # Fetch strategy data
    print("📊 Fetching IBIT data...")
    try:
        strategy_data = data_fetcher.get_strategy_data(start_date, end_date, use_cache=True)
        
        if strategy_data.empty:
            print("❌ No data available for analysis period.")
            return
            
        print(f"✅ Successfully fetched {len(strategy_data)} trading opportunities")
        print()
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return
    
    # Run backtest
    print("🔄 Running backtest...")
    try:
        trade_results, metrics, rolling_metrics = backtester.run_backtest(strategy_data, strategy)
        
        if trade_results.empty:
            print("❌ No trades executed during backtest.")
            return
            
        print(f"✅ Backtest completed with {len(trade_results)} executed trades")
        print()
        
    except Exception as e:
        print(f"❌ Error running backtest: {e}")
        return
    
    # Print performance summary
    backtester.print_performance_summary(metrics)
    
    # Additional detailed analysis
    print("\n" + "=" * 60)
    print("DETAILED ANALYSIS")
    print("=" * 60)
    
    # Monthly performance breakdown
    print(f"\n📊 MONTHLY PERFORMANCE BREAKDOWN")
    trade_results_monthly = trade_results.copy()
    trade_results_monthly['year_month'] = trade_results_monthly['sell_date'].dt.to_period('M')
    monthly_stats = trade_results_monthly.groupby('year_month').agg({
        'net_return': ['count', 'mean', 'sum'],
        'portfolio_value': 'last'
    }).round(4)
    
    monthly_stats.columns = ['Trades', 'Avg_Return', 'Total_Return', 'Portfolio_Value']
    print(monthly_stats.tail(12))  # Show last 12 months
    
    # Drawdown analysis
    print(f"\n📉 DRAWDOWN ANALYSIS")
    portfolio_values = trade_results['portfolio_value']
    running_max = portfolio_values.expanding().max()
    drawdowns = (portfolio_values - running_max) / running_max
    
    # Find significant drawdown periods
    significant_dd = drawdowns[drawdowns < -0.05]  # More than 5% drawdown
    if not significant_dd.empty:
        print(f"Periods with >5% drawdown: {len(significant_dd)}")
        print(f"Average significant drawdown: {significant_dd.mean():.2%}")
        print(f"Longest drawdown period: {len(significant_dd)} trades")
    
    # Performance by market conditions
    print(f"\n📈 PERFORMANCE BY MARKET CONDITIONS")
    
    # Calculate rolling volatility to identify market conditions
    returns_30d = trade_results['net_return'].rolling(30).std()
    high_vol_threshold = returns_30d.quantile(0.7)
    low_vol_threshold = returns_30d.quantile(0.3)
    
    high_vol_mask = returns_30d > high_vol_threshold
    low_vol_mask = returns_30d < low_vol_threshold
    normal_vol_mask = ~(high_vol_mask | low_vol_mask)
    
    if high_vol_mask.any():
        high_vol_performance = trade_results[high_vol_mask]['net_return'].mean()
        print(f"High volatility periods avg return: {high_vol_performance:.2%}")
        
    if low_vol_mask.any():
        low_vol_performance = trade_results[low_vol_mask]['net_return'].mean()
        print(f"Low volatility periods avg return: {low_vol_performance:.2%}")
        
    if normal_vol_mask.any():
        normal_vol_performance = trade_results[normal_vol_mask]['net_return'].mean()
        print(f"Normal volatility periods avg return: {normal_vol_performance:.2%}")
    
    # Rolling performance analysis
    if not rolling_metrics.empty:
        print(f"\n📊 ROLLING PERFORMANCE (30-trade windows)")
        recent_rolling = rolling_metrics.tail(5)
        print("Recent rolling metrics:")
        for _, row in recent_rolling.iterrows():
            print(f"Trade {row['trade_number']}: Win Rate {row['rolling_win_rate']:.1%}, "
                  f"Avg Return {row['rolling_avg_return']:.2%}, "
                  f"Sharpe {row['rolling_sharpe']:.2f}")
    
    # Save results
    print(f"\n💾 SAVING RESULTS")
    try:
        # Create results directory if it doesn't exist
        os.makedirs('results', exist_ok=True)
        
        # Save trade results
        trade_results.to_csv('results/trade_results.csv', index=False)
        print(f"✅ Trade results saved to results/trade_results.csv")
        
        # Save rolling metrics
        if not rolling_metrics.empty:
            rolling_metrics.to_csv('results/rolling_metrics.csv', index=False)
            print(f"✅ Rolling metrics saved to results/rolling_metrics.csv")
        
        # Save performance summary
        summary_df = pd.DataFrame([metrics])
        summary_df.to_csv('results/performance_summary.csv', index=False)
        print(f"✅ Performance summary saved to results/performance_summary.csv")
        
    except Exception as e:
        print(f"⚠️  Error saving results: {e}")
    
    print(f"\n🎉 Analysis Complete!")
    print(f"📋 Summary: {len(trade_results)} trades executed over {metrics['years_traded']:.2f} years")
    print(f"📈 Total Return: {metrics['total_return']:.1%}")
    print(f"📊 Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    
    return trade_results, metrics, rolling_metrics


if __name__ == "__main__":
    results = run_comprehensive_analysis()