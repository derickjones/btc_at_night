"""
Dual Strategy Analysis: IBIT Overnight + MSTR Daytime
Combines overnight IBIT gains with daytime MicroStrategy exposure.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_fetcher import IBITDataFetcher
from backtester import BacktestEngine
import config

def get_mstr_data(start_date, end_date):
    """Fetch MSTR data for the dual strategy."""
    print("📈 Fetching MSTR data...")
    
    mstr = yf.Ticker("MSTR")
    mstr_data = mstr.history(start=start_date, end=end_date)
    
    # Clean and prepare data
    mstr_data = mstr_data.dropna()
    mstr_data.index = mstr_data.index.tz_localize(None)  # Remove timezone for consistency
    
    print(f"✅ MSTR data fetched: {len(mstr_data)} days from {mstr_data.index[0].date()} to {mstr_data.index[-1].date()}")
    
    return mstr_data

def calculate_dual_strategy_performance():
    """Calculate performance of IBIT overnight + MSTR daytime strategy."""
    
    print("🚀 Analyzing Dual Strategy: IBIT Overnight + MSTR Daytime")
    print("=" * 60)
    
    # Load existing IBIT trade results
    ibit_trades = pd.read_csv('results/trade_results.csv')
    ibit_trades['buy_date'] = pd.to_datetime(ibit_trades['buy_date'], utc=True).dt.tz_localize(None)
    ibit_trades['sell_date'] = pd.to_datetime(ibit_trades['sell_date'], utc=True).dt.tz_localize(None)
    
    # Get MSTR data for the same period
    start_date = ibit_trades['buy_date'].iloc[0]
    end_date = ibit_trades['sell_date'].iloc[-1]
    
    mstr_data = get_mstr_data(start_date, end_date)
    
    # Initialize dual strategy tracking
    initial_capital = config.INITIAL_CAPITAL
    portfolio_value = initial_capital
    
    dual_trades = []
    
    print(f"💰 Starting capital: ${initial_capital:,.2f}")
    print(f"📅 Analysis period: {start_date.date()} to {end_date.date()}")
    print(f"🔄 Total IBIT overnight trades: {len(ibit_trades)}")
    
    for i, ibit_trade in ibit_trades.iterrows():
        buy_date = ibit_trade['buy_date']
        sell_date = ibit_trade['sell_date']
        
        # IBIT overnight return (already calculated)
        ibit_overnight_return = ibit_trade['net_return']
        
        # Calculate MSTR daytime return (buy at open, sell at close on same day)
        # Find the corresponding MSTR data for the buy date
        mstr_buy_date = buy_date.date()
        
        # Look for MSTR data on or after the buy date
        mstr_available = mstr_data[mstr_data.index.date >= mstr_buy_date]
        
        if len(mstr_available) == 0:
            # No MSTR data available, skip this trade
            mstr_daytime_return = 0.0
            mstr_open_price = np.nan
            mstr_close_price = np.nan
        else:
            # Use the first available MSTR day (usually same day or next trading day)
            mstr_day = mstr_available.iloc[0]
            mstr_open_price = mstr_day['Open']
            mstr_close_price = mstr_day['Close']
            
            # Calculate MSTR daytime return (with slippage)
            mstr_gross_return = (mstr_close_price - mstr_open_price) / mstr_open_price
            mstr_daytime_return = mstr_gross_return - config.SLIPPAGE  # Apply slippage cost
        
        # Combined strategy return
        # Portfolio is split: some in IBIT overnight, some in MSTR daytime
        # Since they use the same capital at different times, returns are additive
        combined_return = ibit_overnight_return + mstr_daytime_return
        
        # Update portfolio value
        new_portfolio_value = portfolio_value * (1 + combined_return)
        
        # Record the combined trade
        dual_trade = {
            'trade_number': i + 1,
            'buy_date': buy_date,
            'sell_date': sell_date,
            'ibit_buy_price': ibit_trade['buy_price'],
            'ibit_sell_price': ibit_trade['sell_price'],
            'ibit_overnight_return': ibit_overnight_return,
            'mstr_open_price': mstr_open_price,
            'mstr_close_price': mstr_close_price,
            'mstr_daytime_return': mstr_daytime_return,
            'combined_return': combined_return,
            'portfolio_value_before': portfolio_value,
            'portfolio_value_after': new_portfolio_value
        }
        
        dual_trades.append(dual_trade)
        portfolio_value = new_portfolio_value
        
        # Print progress every 50 trades
        if (i + 1) % 50 == 0:
            print(f"📊 Processed {i + 1} trades, Portfolio: ${portfolio_value:,.2f}")
    
    # Convert to DataFrame
    dual_df = pd.DataFrame(dual_trades)
    
    # Save results
    dual_df.to_csv('results/dual_strategy_trades.csv', index=False)
    
    print(f"✅ Dual strategy analysis complete!")
    print(f"📁 Results saved to: results/dual_strategy_trades.csv")
    
    return dual_df

def calculate_dual_performance_metrics(dual_df):
    """Calculate performance metrics for the dual strategy."""
    
    print("\n📊 Calculating Dual Strategy Performance Metrics")
    print("=" * 50)
    
    # Basic metrics
    initial_value = dual_df['portfolio_value_before'].iloc[0]
    final_value = dual_df['portfolio_value_after'].iloc[-1]
    total_return = (final_value - initial_value) / initial_value
    
    # Time-based metrics
    start_date = dual_df['buy_date'].iloc[0]
    end_date = dual_df['sell_date'].iloc[-1]
    days = (end_date - start_date).days
    years = days / 365.25
    annualized_return = (1 + total_return) ** (1/years) - 1
    
    # Return statistics
    returns = dual_df['combined_return']
    mean_return = returns.mean()
    volatility = returns.std() * np.sqrt(252)  # Annualized volatility
    
    # Risk metrics
    portfolio_values = dual_df['portfolio_value_after']
    running_max = portfolio_values.expanding().max()
    drawdowns = (portfolio_values - running_max) / running_max
    max_drawdown = drawdowns.min()
    
    # Performance ratios
    sharpe_ratio = (annualized_return - 0.02) / volatility  # Assume 2% risk-free rate
    calmar_ratio = annualized_return / abs(max_drawdown)
    
    # Trade statistics
    winning_trades = (returns > 0).sum()
    total_trades = len(returns)
    win_rate = winning_trades / total_trades
    
    # Component analysis
    ibit_component = dual_df['ibit_overnight_return'].sum()
    mstr_component = dual_df['mstr_daytime_return'].sum()
    
    # Create performance summary
    performance = {
        'strategy': 'IBIT Overnight + MSTR Daytime',
        'initial_capital': initial_value,
        'final_value': final_value,
        'total_return': total_return,
        'annualized_return': annualized_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'calmar_ratio': calmar_ratio,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'analysis_period_days': days,
        'analysis_period_years': years,
        'ibit_contribution': ibit_component,
        'mstr_contribution': mstr_component
    }
    
    # Print results
    print(f"🎯 Dual Strategy Performance:")
    print(f"   Initial Capital: ${initial_value:,.2f}")
    print(f"   Final Value: ${final_value:,.2f}")
    print(f"   Total Return: {total_return:.1%}")
    print(f"   Annualized Return: {annualized_return:.1%}")
    print(f"   Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"   Max Drawdown: {max_drawdown:.1%}")
    print(f"   Win Rate: {win_rate:.1%}")
    
    print(f"\n🔍 Component Analysis:")
    print(f"   IBIT Overnight Contribution: {ibit_component:.1%}")
    print(f"   MSTR Daytime Contribution: {mstr_component:.1%}")
    print(f"   Combined Effect: {ibit_component + mstr_component:.1%}")
    
    # Save performance metrics
    performance_df = pd.DataFrame([performance])
    performance_df.to_csv('results/dual_strategy_performance.csv', index=False)
    
    return performance

def compare_all_strategies():
    """Compare all strategy variations."""
    
    print("\n🏆 Strategy Comparison Analysis")
    print("=" * 40)
    
    # Load all performance data
    ibit_only = pd.read_csv('results/performance_summary.csv')
    dual_perf = pd.read_csv('results/dual_strategy_performance.csv')
    
    # Load MSTR data for standalone comparison
    ibit_trades = pd.read_csv('results/trade_results.csv')
    start_date = pd.to_datetime(ibit_trades['buy_date'].iloc[0], utc=True).dt.tz_localize(None)
    end_date = pd.to_datetime(ibit_trades['sell_date'].iloc[-1], utc=True).dt.tz_localize(None)
    
    mstr_data = get_mstr_data(start_date, end_date)
    mstr_start_price = mstr_data['Close'].iloc[0]
    mstr_end_price = mstr_data['Close'].iloc[-1]
    mstr_total_return = (mstr_end_price - mstr_start_price) / mstr_start_price
    
    days = (end_date - start_date).days
    years = days / 365.25
    mstr_annualized = (1 + mstr_total_return) ** (1/years) - 1
    
    # Create comparison table
    comparison_data = {
        'Strategy': [
            'IBIT Overnight Only',
            'MSTR Buy & Hold',
            'IBIT Overnight + MSTR Daytime',
            'Improvement vs IBIT Only'
        ],
        'Total Return': [
            f"{ibit_only['total_return'].iloc[0]:.1%}",
            f"{mstr_total_return:.1%}",
            f"{dual_perf['total_return'].iloc[0]:.1%}",
            f"+{(dual_perf['total_return'].iloc[0] - ibit_only['total_return'].iloc[0]):.1%}"
        ],
        'Annualized Return': [
            f"{ibit_only['annualized_return'].iloc[0]:.1%}",
            f"{mstr_annualized:.1%}",
            f"{dual_perf['annualized_return'].iloc[0]:.1%}",
            f"+{(dual_perf['annualized_return'].iloc[0] - ibit_only['annualized_return'].iloc[0]):.1%}"
        ],
        'Sharpe Ratio': [
            f"{ibit_only['sharpe_ratio'].iloc[0]:.2f}",
            "N/A",
            f"{dual_perf['sharpe_ratio'].iloc[0]:.2f}",
            f"+{(dual_perf['sharpe_ratio'].iloc[0] - ibit_only['sharpe_ratio'].iloc[0]):.2f}"
        ]
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    print("\n📊 Performance Comparison:")
    print(comparison_df.to_string(index=False))
    
    # Save comparison
    comparison_df.to_csv('results/strategy_comparison_with_dual.csv', index=False)
    
    # Answer the key question
    ibit_annual = ibit_only['annualized_return'].iloc[0]
    dual_annual = dual_perf['annualized_return'].iloc[0]
    mstr_annual = mstr_annualized
    
    additional_return = dual_annual - ibit_annual
    mstr_capture_rate = additional_return / mstr_annual if mstr_annual != 0 else 0
    
    print(f"\n💡 Key Findings:")
    print(f"   MSTR Buy & Hold Annual Return: {mstr_annual:.1%}")
    print(f"   Additional Return from Dual Strategy: {additional_return:.1%}")
    print(f"   MSTR Capture Rate: {mstr_capture_rate:.1%}")
    print(f"   Capital Efficiency: {'Excellent' if mstr_capture_rate > 0.8 else 'Good' if mstr_capture_rate > 0.5 else 'Moderate'}")
    
    return comparison_df

if __name__ == "__main__":
    # Run the dual strategy analysis
    dual_trades_df = calculate_dual_strategy_performance()
    dual_performance = calculate_dual_performance_metrics(dual_trades_df)
    comparison_results = compare_all_strategies()
    
    print(f"\n🎉 Dual Strategy Analysis Complete!")
    print(f"📁 Results saved in results/ directory")
    print(f"📊 Check dual_strategy_trades.csv for detailed trade data")
    print(f"📈 Check dual_strategy_performance.csv for performance metrics")
    print(f"🏆 Check strategy_comparison_with_dual.csv for strategy comparison")