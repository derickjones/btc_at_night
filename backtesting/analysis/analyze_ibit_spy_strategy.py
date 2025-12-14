"""
IBIT Overnight + SPY Day Trading Strategy Analysis
Models combining IBIT overnight gains with SPY daytime trading.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import sys
import os

# Add core directory to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core'))

import config

def get_spy_data(start_date, end_date):
    """Fetch SPY data for the analysis period."""
    print("📈 Fetching SPY data for day trading analysis...")
    
    spy = yf.Ticker("SPY")
    spy_data = spy.history(start=start_date, end=end_date)
    
    # Clean and prepare data
    spy_data = spy_data.dropna()
    spy_data.index = spy_data.index.tz_localize(None)  # Remove timezone for consistency
    
    print(f"✅ SPY data fetched: {len(spy_data)} days from {spy_data.index[0].date()} to {spy_data.index[-1].date()}")
    
    return spy_data

def calculate_spy_day_trading_returns(spy_data):
    """Calculate SPY intraday returns (open to close)."""
    
    # Calculate intraday returns (9:30 AM to 4:00 PM equivalent)
    # Using Open to Close as proxy for 9:35 AM to 3:55 PM trading
    spy_data['day_return_gross'] = (spy_data['Close'] - spy_data['Open']) / spy_data['Open']
    
    # Apply transaction costs
    SPY_SPREAD_COST = 0.00004  # 0.004% round trip (very tight spreads)
    spy_data['day_return_net'] = spy_data['day_return_gross'] - SPY_SPREAD_COST
    
    return spy_data

def calculate_ibit_spy_combined_strategy():
    """Calculate the combined IBIT overnight + SPY day trading strategy."""
    
    print("🚀 Analyzing IBIT Overnight + SPY Day Trading Strategy")
    print("=" * 65)
    
    # Load existing IBIT trade results
    ibit_trades = pd.read_csv('results/trade_results.csv')
    ibit_trades['buy_date'] = pd.to_datetime(ibit_trades['buy_date'], utc=True).dt.tz_localize(None)
    ibit_trades['sell_date'] = pd.to_datetime(ibit_trades['sell_date'], utc=True).dt.tz_localize(None)
    
    # Get SPY data for the same period
    start_date = ibit_trades['buy_date'].iloc[0]
    end_date = ibit_trades['sell_date'].iloc[-1]
    
    spy_data = get_spy_data(start_date, end_date)
    spy_data = calculate_spy_day_trading_returns(spy_data)
    
    # Initialize combined strategy tracking
    initial_capital = config.INITIAL_CAPITAL
    portfolio_value = initial_capital
    
    combined_trades = []
    
    print(f"💰 Starting capital: ${initial_capital:,.2f}")
    print(f"📅 Analysis period: {start_date.date()} to {end_date.date()}")
    print(f"🔄 Total IBIT overnight trades: {len(ibit_trades)}")
    print(f"📊 SPY trading days available: {len(spy_data)}")
    
    for i, ibit_trade in ibit_trades.iterrows():
        buy_date = ibit_trade['buy_date']
        sell_date = ibit_trade['sell_date']
        
        # IBIT overnight return (already calculated)
        ibit_overnight_return = ibit_trade['net_return']
        
        # Find corresponding SPY day trading return
        # Look for SPY data on the buy_date (when we'd be trading SPY during the day)
        spy_buy_date = buy_date.date()
        
        # Find SPY data for this date
        spy_day_data = spy_data[spy_data.index.date == spy_buy_date]
        
        if len(spy_day_data) > 0:
            # SPY market was open that day
            spy_day_return = spy_day_data.iloc[0]['day_return_net']
            spy_open = spy_day_data.iloc[0]['Open']
            spy_close = spy_day_data.iloc[0]['Close']
            spy_traded = True
        else:
            # No SPY trading that day (market closed, holiday, etc.)
            spy_day_return = 0.0
            spy_open = np.nan
            spy_close = np.nan
            spy_traded = False
        
        # Combined strategy return
        # Capital flow: Start day with cash -> Buy SPY at 9:35 -> Sell SPY at 3:55 -> Buy IBIT at 4:00 -> Sell IBIT at 9:30 next day
        combined_return = ibit_overnight_return + spy_day_return
        
        # Update portfolio value
        new_portfolio_value = portfolio_value * (1 + combined_return)
        
        # Record the combined trade
        combined_trade = {
            'trade_number': i + 1,
            'date': buy_date,
            'ibit_buy_price': ibit_trade['buy_price'],
            'ibit_sell_price': ibit_trade['sell_price'],
            'ibit_overnight_return': ibit_overnight_return,
            'spy_open': spy_open,
            'spy_close': spy_close,
            'spy_day_return': spy_day_return,
            'spy_traded': spy_traded,
            'combined_return': combined_return,
            'portfolio_value_before': portfolio_value,
            'portfolio_value_after': new_portfolio_value
        }
        
        combined_trades.append(combined_trade)
        portfolio_value = new_portfolio_value
        
        # Progress update
        if (i + 1) % 50 == 0:
            print(f"📈 Processed {i + 1} trades, Portfolio: ${portfolio_value:,.2f}")
    
    # Convert to DataFrame
    combined_df = pd.DataFrame(combined_trades)
    
    # Save results
    combined_df.to_csv('results/ibit_spy_combined_strategy.csv', index=False)
    
    print(f"✅ IBIT + SPY combined strategy analysis complete!")
    print(f"📁 Results saved to: results/ibit_spy_combined_strategy.csv")
    
    return combined_df

def calculate_performance_metrics(combined_df):
    """Calculate comprehensive performance metrics for IBIT + SPY strategy."""
    
    print("\n📊 IBIT + SPY Performance Analysis")
    print("=" * 45)
    
    # Basic performance
    initial_value = combined_df['portfolio_value_before'].iloc[0]
    final_value = combined_df['portfolio_value_after'].iloc[-1]
    total_return = (final_value - initial_value) / initial_value
    
    # Time metrics
    start_date = combined_df['date'].iloc[0]
    end_date = combined_df['date'].iloc[-1]
    days = (end_date - start_date).days
    years = days / 365.25
    annualized_return = (1 + total_return) ** (1/years) - 1
    
    # Component analysis
    ibit_total = combined_df['ibit_overnight_return'].sum()
    spy_total = combined_df['spy_day_return'].sum()
    
    # Filter out days when SPY wasn't traded
    spy_traded_days = combined_df[combined_df['spy_traded'] == True]
    spy_win_rate = (spy_traded_days['spy_day_return'] > 0).mean()
    spy_trading_days = len(spy_traded_days)
    
    # Risk metrics
    returns = combined_df['combined_return']
    volatility = returns.std() * np.sqrt(252)
    sharpe_ratio = (annualized_return - 0.02) / volatility if volatility > 0 else 0
    
    # Drawdown analysis
    portfolio_values = combined_df['portfolio_value_after']
    running_max = portfolio_values.expanding().max()
    drawdowns = (portfolio_values - running_max) / running_max
    max_drawdown = drawdowns.min()
    
    # Trade statistics
    win_rate = (returns > 0).mean()
    
    # SPY statistics
    spy_returns = spy_traded_days['spy_day_return']
    spy_avg_return = spy_returns.mean()
    spy_volatility = spy_returns.std() * np.sqrt(252)
    
    # Annualized component contributions
    ibit_annual = (1 + ibit_total) ** (1/years) - 1
    spy_annual = (1 + spy_total) ** (1/years) - 1
    
    # Print comprehensive results
    print(f"🎯 Combined Strategy Results:")
    print(f"   Analysis Period: {days} days ({years:.2f} years)")
    print(f"   Initial Value: ${initial_value:,.2f}")
    print(f"   Final Value: ${final_value:,.2f}")
    print(f"   Total Return: {total_return:.1%}")
    print(f"   Annualized Return: {annualized_return:.1%}")
    print(f"   Volatility: {volatility:.1%}")
    print(f"   Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"   Max Drawdown: {max_drawdown:.1%}")
    print(f"   Overall Win Rate: {win_rate:.1%}")
    
    print(f"\n🔍 Component Analysis (Annualized):")
    print(f"   IBIT Overnight: {ibit_annual:.1%}")
    print(f"   SPY Day Trading: {spy_annual:.1%}")
    print(f"   Combined Total: {annualized_return:.1%}")
    print(f"   Improvement vs IBIT-only: {spy_annual:+.1%}")
    
    print(f"\n📊 SPY Day Trading Statistics:")
    print(f"   Trading Days: {spy_trading_days}")
    print(f"   SPY Win Rate: {spy_win_rate:.1%}")
    print(f"   SPY Avg Daily Return: {spy_avg_return:.3%}")
    print(f"   SPY Daily Volatility: {spy_volatility:.1%}")
    print(f"   Best SPY Day: {spy_returns.max():.2%}")
    print(f"   Worst SPY Day: {spy_returns.min():.2%}")
    
    # Save performance metrics
    performance = {
        'strategy': 'IBIT Overnight + SPY Day Trading',
        'analysis_period_days': days,
        'analysis_period_years': years,
        'total_return': total_return,
        'annualized_return': annualized_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'ibit_contribution_annual': ibit_annual,
        'spy_contribution_annual': spy_annual,
        'spy_win_rate': spy_win_rate,
        'spy_trading_days': spy_trading_days,
        'spy_avg_daily_return': spy_avg_return,
        'spy_volatility': spy_volatility
    }
    
    performance_df = pd.DataFrame([performance])
    performance_df.to_csv('results/ibit_spy_performance.csv', index=False)
    
    return performance

def compare_all_strategies():
    """Compare IBIT-only vs IBIT+SPY vs other strategies."""
    
    print("\n🏆 Strategy Comparison Analysis")
    print("=" * 35)
    
    try:
        # Load performance data
        ibit_only = pd.read_csv('results/performance_summary.csv')
        combined_perf = pd.read_csv('results/ibit_spy_performance.csv')
        
        # Load SPY buy & hold for comparison
        ibit_trades = pd.read_csv('results/trade_results.csv')
        start_date = pd.to_datetime(ibit_trades['buy_date'].iloc[0], utc=True).dt.tz_localize(None)
        end_date = pd.to_datetime(ibit_trades['sell_date'].iloc[-1], utc=True).dt.tz_localize(None)
        
        spy = yf.Ticker("SPY")
        spy_data = spy.history(start=start_date, end=end_date)
        spy_start_price = spy_data['Close'].iloc[0]
        spy_end_price = spy_data['Close'].iloc[-1]
        spy_total_return = (spy_end_price - spy_start_price) / spy_start_price
        
        days = (end_date - start_date).days
        years = days / 365.25
        spy_annualized = (1 + spy_total_return) ** (1/years) - 1
        
        print(f"📊 Strategy Performance Comparison:")
        print(f"   IBIT Overnight Only: {ibit_only['annualized_return'].iloc[0]:.1%}")
        print(f"   SPY Buy & Hold: {spy_annualized:.1%}")
        print(f"   IBIT + SPY Combined: {combined_perf['annualized_return'].iloc[0]:.1%}")
        
        improvement = combined_perf['annualized_return'].iloc[0] - ibit_only['annualized_return'].iloc[0]
        print(f"   Improvement vs IBIT-only: {improvement:+.1%}")
        
        print(f"\n🎯 Risk-Adjusted Comparison:")
        print(f"   IBIT-only Sharpe: {ibit_only['sharpe_ratio'].iloc[0]:.2f}")
        print(f"   IBIT+SPY Sharpe: {combined_perf['sharpe_ratio'].iloc[0]:.2f}")
        
        print(f"\n💡 Key Insights:")
        spy_contribution = combined_perf['spy_contribution_annual'].iloc[0]
        if spy_contribution > 0.02:  # More than 2%
            assessment = "Significant positive contribution"
        elif spy_contribution > 0:
            assessment = "Modest positive contribution"
        else:
            assessment = "Negative contribution - hurt performance"
        
        print(f"   SPY Day Trading: {spy_contribution:+.1%} ({assessment})")
        print(f"   SPY Win Rate: {combined_perf['spy_win_rate'].iloc[0]:.1%}")
        print(f"   Strategy Complexity: Doubled (4 trades vs 2 daily)")
        
        return {
            'ibit_only': ibit_only['annualized_return'].iloc[0],
            'spy_only': spy_annualized,
            'combined': combined_perf['annualized_return'].iloc[0],
            'improvement': improvement,
            'spy_contribution': spy_contribution
        }
        
    except Exception as e:
        print(f"Error in comparison: {e}")
        return None

if __name__ == "__main__":
    # Run the combined strategy analysis
    combined_df = calculate_ibit_spy_combined_strategy()
    performance = calculate_performance_metrics(combined_df)
    comparison = compare_all_strategies()
    
    print(f"\n🎉 IBIT + SPY Combined Strategy Analysis Complete!")
    print(f"📁 Detailed results saved in results/ directory")
    print(f"📊 Check ibit_spy_combined_strategy.csv for trade-by-trade data")
    print(f"📈 Check ibit_spy_performance.csv for performance metrics")