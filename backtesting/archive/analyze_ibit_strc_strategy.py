"""
IBIT Overnight + STRC Dividend Strategy Analysis
Combines overnight IBIT gains with daytime STRC dividend collection.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import config

def get_overlapping_period_data():
    """Get IBIT and STRC data for the overlapping period."""
    print("📊 Finding overlapping data period for IBIT + STRC analysis...")
    
    # Load existing IBIT trade results
    ibit_trades = pd.read_csv('results/trade_results.csv')
    ibit_trades['buy_date'] = pd.to_datetime(ibit_trades['buy_date'], utc=True).dt.tz_localize(None)
    ibit_trades['sell_date'] = pd.to_datetime(ibit_trades['sell_date'], utc=True).dt.tz_localize(None)
    
    # Get STRC data
    strc = yf.Ticker("STRC")
    strc_data = strc.history(start="2025-07-01", end="2025-12-12")
    strc_data.index = strc_data.index.tz_localize(None)
    
    # Find overlapping period
    strc_start = strc_data.index[0]
    strc_end = strc_data.index[-1]
    
    ibit_start = ibit_trades['buy_date'].min()
    ibit_end = ibit_trades['sell_date'].max()
    
    # Use overlapping period
    overlap_start = max(strc_start, ibit_start)
    overlap_end = min(strc_end, ibit_end)
    
    print(f"📅 Analysis Period: {overlap_start.date()} to {overlap_end.date()}")
    print(f"📈 STRC data: {len(strc_data)} days")
    
    # Filter IBIT trades to overlapping period
    overlap_trades = ibit_trades[
        (ibit_trades['buy_date'] >= overlap_start) & 
        (ibit_trades['sell_date'] <= overlap_end)
    ].copy()
    
    print(f"🔄 IBIT trades in overlap period: {len(overlap_trades)}")
    
    return overlap_trades, strc_data, overlap_start, overlap_end

def calculate_strc_dividend_strategy():
    """Calculate the combined IBIT overnight + STRC dividend strategy."""
    
    print("🚀 Analyzing IBIT Overnight + STRC Dividend Strategy")
    print("=" * 60)
    
    # Get overlapping data
    ibit_trades, strc_data, start_date, end_date = get_overlapping_period_data()
    
    if len(ibit_trades) == 0:
        print("❌ No overlapping IBIT trades found!")
        return None
    
    # STRC dividend parameters
    ANNUAL_DIVIDEND_RATE = 0.1075  # 10.75%
    DAILY_DIVIDEND_RATE = ANNUAL_DIVIDEND_RATE / 365  # Daily accrual rate
    
    # Initialize tracking
    initial_capital = config.INITIAL_CAPITAL
    portfolio_value = initial_capital
    
    # Reset portfolio value based on first trade date if needed
    first_trade_date = ibit_trades.iloc[0]['buy_date']
    if len(ibit_trades) > 0:
        # Find the portfolio value at the start of our overlap period
        all_trades = pd.read_csv('results/trade_results.csv')
        all_trades['buy_date'] = pd.to_datetime(all_trades['buy_date'], utc=True).dt.tz_localize(None)
        
        # Find the last trade before our overlap period
        prior_trades = all_trades[all_trades['buy_date'] < first_trade_date]
        if len(prior_trades) > 0:
            portfolio_value = prior_trades.iloc[-1]['portfolio_value']
            print(f"💰 Starting portfolio value (from prior trades): ${portfolio_value:,.2f}")
        else:
            print(f"💰 Starting with initial capital: ${portfolio_value:,.2f}")
    
    combined_trades = []
    
    print(f"📊 Processing {len(ibit_trades)} trades...")
    
    for i, ibit_trade in ibit_trades.iterrows():
        buy_date = ibit_trade['buy_date']
        sell_date = ibit_trade['sell_date']
        
        # IBIT overnight return (already calculated)
        ibit_overnight_return = ibit_trade['net_return']
        
        # Calculate STRC dividend accrual for the day
        # Strategy: buy STRC at market open, hold during day, sell at close
        # Accrues dividend at daily rate
        
        # Find STRC data for the corresponding day
        buy_date_only = buy_date.date()
        strc_day_data = strc_data[strc_data.index.date == buy_date_only]
        
        if len(strc_day_data) > 0:
            # STRC was trading that day
            strc_open = strc_day_data.iloc[0]['Open']
            strc_close = strc_day_data.iloc[0]['Close']
            
            # Price appreciation/depreciation during the day
            strc_price_return = (strc_close - strc_open) / strc_open
            
            # Dividend accrual (prorated daily)
            strc_dividend_return = DAILY_DIVIDEND_RATE
            
            # Total STRC return for the day
            strc_total_return = strc_price_return + strc_dividend_return - config.SLIPPAGE
            
        else:
            # No STRC data for that day (market closed, etc.)
            strc_open = np.nan
            strc_close = np.nan
            strc_price_return = 0.0
            strc_dividend_return = 0.0
            strc_total_return = 0.0
        
        # Combined strategy return
        # Capital is used for both strategies in sequence:
        # 1. Buy STRC at market open, sell at close (day return)
        # 2. Buy IBIT at market close, sell next morning (overnight return)
        combined_return = ibit_overnight_return + strc_total_return
        
        # Update portfolio value
        new_portfolio_value = portfolio_value * (1 + combined_return)
        
        # Record the trade
        combined_trade = {
            'trade_number': len(combined_trades) + 1,
            'date': buy_date,
            'ibit_buy_price': ibit_trade['buy_price'],
            'ibit_sell_price': ibit_trade['sell_price'], 
            'ibit_overnight_return': ibit_overnight_return,
            'strc_open_price': strc_open,
            'strc_close_price': strc_close,
            'strc_price_return': strc_price_return,
            'strc_dividend_return': strc_dividend_return,
            'strc_total_return': strc_total_return,
            'combined_return': combined_return,
            'portfolio_value_before': portfolio_value,
            'portfolio_value_after': new_portfolio_value
        }
        
        combined_trades.append(combined_trade)
        portfolio_value = new_portfolio_value
        
        # Progress update
        if len(combined_trades) % 20 == 0:
            print(f"📈 Processed {len(combined_trades)} trades, Portfolio: ${portfolio_value:,.2f}")
    
    # Convert to DataFrame
    combined_df = pd.DataFrame(combined_trades)
    
    # Save results
    combined_df.to_csv('results/ibit_strc_combined_strategy.csv', index=False)
    
    print(f"✅ Combined strategy analysis complete!")
    print(f"📁 Results saved to: results/ibit_strc_combined_strategy.csv")
    
    return combined_df, start_date, end_date

def calculate_performance_metrics(combined_df, start_date, end_date):
    """Calculate comprehensive performance metrics."""
    
    print("\n📊 Performance Analysis")
    print("=" * 40)
    
    # Basic performance
    initial_value = combined_df['portfolio_value_before'].iloc[0]
    final_value = combined_df['portfolio_value_after'].iloc[-1]
    total_return = (final_value - initial_value) / initial_value
    
    # Annualized metrics
    days = (end_date - start_date).days
    years = days / 365.25
    annualized_return = (1 + total_return) ** (1/years) - 1
    
    # Component analysis
    ibit_total = combined_df['ibit_overnight_return'].sum()
    strc_dividend_total = combined_df['strc_dividend_return'].sum()
    strc_price_total = combined_df['strc_price_return'].sum()
    strc_total = combined_df['strc_total_return'].sum()
    
    # Risk metrics
    returns = combined_df['combined_return']
    volatility = returns.std() * np.sqrt(252)
    sharpe_ratio = (annualized_return - 0.02) / volatility
    
    # Drawdown analysis
    portfolio_values = combined_df['portfolio_value_after']
    running_max = portfolio_values.expanding().max()
    drawdowns = (portfolio_values - running_max) / running_max
    max_drawdown = drawdowns.min()
    
    # Trade statistics
    win_rate = (returns > 0).mean()
    
    # Annualized component contributions
    ibit_annual = (1 + ibit_total) ** (1/years) - 1
    strc_dividend_annual = (1 + strc_dividend_total) ** (1/years) - 1
    strc_price_annual = (1 + strc_price_total) ** (1/years) - 1
    strc_total_annual = (1 + strc_total) ** (1/years) - 1
    
    # Print results
    print(f"🎯 Combined Strategy Results:")
    print(f"   Analysis Period: {days} days ({years:.2f} years)")
    print(f"   Initial Value: ${initial_value:,.2f}")
    print(f"   Final Value: ${final_value:,.2f}")
    print(f"   Total Return: {total_return:.1%}")
    print(f"   Annualized Return: {annualized_return:.1%}")
    print(f"   Volatility: {volatility:.1%}")
    print(f"   Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"   Max Drawdown: {max_drawdown:.1%}")
    print(f"   Win Rate: {win_rate:.1%}")
    
    print(f"\n🔍 Component Analysis (Annualized):")
    print(f"   IBIT Overnight: {ibit_annual:.1%}")
    print(f"   STRC Dividends: {strc_dividend_annual:.1%}")
    print(f"   STRC Price: {strc_price_annual:.1%}")
    print(f"   STRC Total: {strc_total_annual:.1%}")
    print(f"   Combined Total: {annualized_return:.1%}")
    
    # Calculate theoretical maximum if STRC paid full 10.75%
    theoretical_strc_annual = 0.1075
    theoretical_combined = ibit_annual + theoretical_strc_annual
    capture_rate = strc_total_annual / theoretical_strc_annual if theoretical_strc_annual > 0 else 0
    
    print(f"\n💡 STRC Dividend Analysis:")
    print(f"   Theoretical STRC yield: {theoretical_strc_annual:.1%}")
    print(f"   Actual STRC contribution: {strc_total_annual:.1%}")
    print(f"   Capture rate: {capture_rate:.1%}")
    print(f"   Theoretical combined: {theoretical_combined:.1%}")
    print(f"   Actual combined: {annualized_return:.1%}")
    
    # Save performance summary
    performance = {
        'strategy': 'IBIT Overnight + STRC Dividend',
        'analysis_period_days': days,
        'analysis_period_years': years,
        'total_return': total_return,
        'annualized_return': annualized_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'ibit_contribution_annual': ibit_annual,
        'strc_dividend_contribution_annual': strc_dividend_annual,
        'strc_price_contribution_annual': strc_price_annual,
        'strc_total_contribution_annual': strc_total_annual,
        'strc_capture_rate': capture_rate,
        'theoretical_strc_yield': theoretical_strc_annual,
        'theoretical_combined_return': theoretical_combined
    }
    
    performance_df = pd.DataFrame([performance])
    performance_df.to_csv('results/ibit_strc_performance.csv', index=False)
    
    return performance

def compare_strategies():
    """Compare all strategy variants."""
    
    print("\n🏆 Strategy Comparison")
    print("=" * 30)
    
    try:
        # Load performance data
        ibit_only = pd.read_csv('results/performance_summary.csv')
        combined_perf = pd.read_csv('results/ibit_strc_performance.csv')
        
        # Load STRC-only performance for comparison
        strc = yf.Ticker("STRC")
        strc_data = strc.history(start="2025-07-30", end="2025-12-12")
        
        strc_start_price = strc_data['Close'].iloc[0]
        strc_end_price = strc_data['Close'].iloc[-1]
        strc_days = len(strc_data)
        strc_years = strc_days / 365.25
        
        strc_price_return = (strc_end_price - strc_start_price) / strc_start_price
        strc_dividend_return = 0.1075 * strc_years  # Pro-rated dividend
        strc_total_return = strc_price_return + strc_dividend_return
        strc_annualized = (1 + strc_total_return) ** (1/strc_years) - 1
        
        print(f"📊 Strategy Comparison:")
        print(f"   IBIT Overnight Only: {ibit_only['annualized_return'].iloc[0]:.1%}")
        print(f"   STRC Only (est.): {strc_annualized:.1%}")
        print(f"   IBIT + STRC Combined: {combined_perf['annualized_return'].iloc[0]:.1%}")
        
        improvement = combined_perf['annualized_return'].iloc[0] - ibit_only['annualized_return'].iloc[0]
        print(f"   Improvement over IBIT-only: +{improvement:.1%}")
        
        print(f"\n🎯 Key Insights:")
        capture_rate = combined_perf['strc_capture_rate'].iloc[0]
        if capture_rate > 0.8:
            efficiency = "Excellent"
        elif capture_rate > 0.6:
            efficiency = "Good"  
        else:
            efficiency = "Moderate"
        
        print(f"   STRC dividend capture: {capture_rate:.1%} ({efficiency})")
        print(f"   Capital efficiency: High (dual deployment)")
        
        return {
            'ibit_only': ibit_only['annualized_return'].iloc[0],
            'strc_only': strc_annualized,
            'combined': combined_perf['annualized_return'].iloc[0],
            'improvement': improvement,
            'capture_rate': capture_rate
        }
        
    except Exception as e:
        print(f"Error in comparison: {e}")
        return None

if __name__ == "__main__":
    # Run the analysis
    combined_df, start_date, end_date = calculate_strc_dividend_strategy()
    
    if combined_df is not None:
        performance = calculate_performance_metrics(combined_df, start_date, end_date)
        comparison = compare_strategies()
        
        print(f"\n🎉 IBIT + STRC Strategy Analysis Complete!")
        print(f"📁 Detailed results saved in results/ directory")
    else:
        print(f"❌ Analysis could not be completed - insufficient data overlap")