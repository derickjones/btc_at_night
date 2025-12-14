"""
Strategy comparison module - calculates alternative strategies for comparison.
"""

import pandas as pd
import numpy as np
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from data_fetcher import IBITDataFetcher
from strategy import IBITOvernightStrategy
from backtester import BacktestEngine
import config

class StrategyComparer:
    """Compare different trading strategies."""
    
    def __init__(self):
        self.data_fetcher = IBITDataFetcher()
        self.backtester = BacktestEngine()
        
    def calculate_day_only_strategy(self, strategy_data):
        """
        Calculate day-only strategy: buy at open, sell at close same day.
        """
        results = []
        initial_capital = config.INITIAL_CAPITAL
        current_capital = initial_capital
        
        for _, row in strategy_data.iterrows():
            # Day strategy: buy at open, sell at close
            buy_price = row['sell_price']  # Open price (from overnight strategy)
            sell_price = row['buy_price']  # Close price (from overnight strategy)
            
            # Calculate shares we can buy
            shares = int(current_capital * (1 - config.SLIPPAGE) / buy_price)
            if shares <= 0:
                continue
                
            # Execute trade
            buy_cost = shares * buy_price * (1 + config.SLIPPAGE)
            sell_proceeds = shares * sell_price * (1 - config.SLIPPAGE)
            
            # Update capital
            current_capital = current_capital - buy_cost + sell_proceeds
            
            # Calculate return
            trade_return = (sell_proceeds - buy_cost) / buy_cost
            gross_return = (sell_price - buy_price) / buy_price
            
            results.append({
                'trade_date': row['trade_date'],
                'buy_date': row['sell_date'],  # Buy at open
                'sell_date': row['buy_date'],  # Sell at close
                'buy_price': buy_price,
                'sell_price': sell_price,
                'shares': shares,
                'buy_cost': buy_cost,
                'sell_proceeds': sell_proceeds,
                'gross_return': gross_return,
                'net_return': trade_return,
                'pnl': sell_proceeds - buy_cost,
                'portfolio_value': current_capital
            })
        
        return pd.DataFrame(results)
    
    def calculate_buy_and_hold_strategy(self, strategy_data):
        """
        Calculate buy-and-hold strategy: buy at start, hold until end.
        """
        if strategy_data.empty:
            return {}
            
        initial_capital = config.INITIAL_CAPITAL
        start_price = strategy_data.iloc[0]['buy_price']  # First close price
        end_price = strategy_data.iloc[-1]['sell_price']   # Last open price
        
        # Calculate shares we could buy at start
        shares = int(initial_capital * (1 - config.SLIPPAGE) / start_price)
        buy_cost = shares * start_price * (1 + config.SLIPPAGE)
        
        # Calculate final value
        final_proceeds = shares * end_price * (1 - config.SLIPPAGE)
        
        total_return = (final_proceeds - buy_cost) / buy_cost
        
        return {
            'initial_capital': initial_capital,
            'start_price': start_price,
            'end_price': end_price,
            'shares': shares,
            'buy_cost': buy_cost,
            'final_value': final_proceeds,
            'total_return': total_return,
            'annualized_return': (final_proceeds / buy_cost) ** (1/1.92) - 1  # ~1.92 years
        }
    
    def run_all_comparisons(self, start_date=config.START_DATE, end_date=config.END_DATE):
        """Run all strategy comparisons."""
        
        print("🔄 Running Strategy Comparisons...")
        print("=" * 50)
        
        # Get base strategy data
        strategy_data = self.data_fetcher.get_strategy_data(start_date, end_date, use_cache=True)
        
        # 1. Overnight Strategy (already calculated)
        overnight_results = pd.read_csv('results/trade_results.csv')
        overnight_results['buy_date'] = pd.to_datetime(overnight_results['buy_date'])
        overnight_results['sell_date'] = pd.to_datetime(overnight_results['sell_date'])
        
        overnight_performance = pd.read_csv('results/performance_summary.csv')
        
        print(f"✅ Overnight Strategy: {overnight_performance['total_return'].iloc[0]:.1%} total return")
        
        # 2. Day-Only Strategy
        print("📈 Calculating Day-Only Strategy...")
        day_results = self.calculate_day_only_strategy(strategy_data)
        
        if not day_results.empty:
            # Calculate performance metrics for day strategy
            day_strategy = IBITOvernightStrategy()
            day_strategy.reset()
            day_strategy.current_capital = day_results['portfolio_value'].iloc[-1]
            
            # Ensure dates are datetime objects
            day_results_copy = day_results.copy()
            day_results_copy['buy_date'] = pd.to_datetime(day_results_copy['buy_date'])
            day_results_copy['sell_date'] = pd.to_datetime(day_results_copy['sell_date'])
            
            day_metrics = self.backtester.calculate_performance_metrics(day_results_copy)
            print(f"✅ Day-Only Strategy: {day_metrics['total_return']:.1%} total return")
        else:
            day_metrics = {}
            print("❌ Day-Only Strategy: No trades executed")
        
        # 3. Buy-and-Hold Strategy
        print("📊 Calculating Buy-and-Hold Strategy...")
        buy_hold_results = self.calculate_buy_and_hold_strategy(strategy_data)
        print(f"✅ Buy-and-Hold Strategy: {buy_hold_results['total_return']:.1%} total return")
        
        # Create comparison summary
        comparison_summary = {
            'Strategy': ['Overnight Only', 'Day Only', 'Buy & Hold'],
            'Total Return': [
                overnight_performance['total_return'].iloc[0],
                day_metrics.get('total_return', 0) if day_metrics else 0,
                buy_hold_results['total_return']
            ],
            'Annualized Return': [
                overnight_performance['annualized_return'].iloc[0],
                day_metrics.get('annualized_return', 0) if day_metrics else 0,
                buy_hold_results['annualized_return']
            ],
            'Sharpe Ratio': [
                overnight_performance['sharpe_ratio'].iloc[0],
                day_metrics.get('sharpe_ratio', 0) if day_metrics else 0,
                'N/A'  # Single position, no volatility
            ],
            'Max Drawdown': [
                overnight_performance['max_drawdown'].iloc[0],
                day_metrics.get('max_drawdown', 0) if day_metrics else 0,
                'N/A'  # Single position
            ],
            'Total Trades': [
                overnight_performance['total_trades'].iloc[0],
                len(day_results) if not day_results.empty else 0,
                1  # Single buy-and-hold
            ]
        }
        
        comparison_df = pd.DataFrame(comparison_summary)
        
        # Save results
        os.makedirs('results', exist_ok=True)
        
        if not day_results.empty:
            day_results.to_csv('results/day_strategy_results.csv', index=False)
            
        pd.DataFrame([day_metrics]).to_csv('results/day_strategy_performance.csv', index=False)
        pd.DataFrame([buy_hold_results]).to_csv('results/buy_hold_performance.csv', index=False)
        comparison_df.to_csv('results/strategy_comparison.csv', index=False)
        
        print(f"\n📊 STRATEGY COMPARISON SUMMARY:")
        print("=" * 50)
        print(comparison_df.to_string(index=False, float_format='%.2f'))
        
        return {
            'overnight': overnight_results,
            'day_only': day_results,
            'buy_hold': buy_hold_results,
            'comparison': comparison_df
        }


if __name__ == "__main__":
    comparer = StrategyComparer()
    results = comparer.run_all_comparisons()
    print("\n🎉 Strategy comparison complete!")