"""
Backtesting engine for IBIT overnight trading strategy.
Calculates comprehensive performance metrics and risk analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import sys
import os
from datetime import datetime

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class BacktestEngine:
    """
    Comprehensive backtesting engine for trading strategies.
    """
    
    def __init__(self, initial_capital: float = config.INITIAL_CAPITAL):
        self.initial_capital = initial_capital
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        
    def calculate_performance_metrics(self, trade_results: pd.DataFrame) -> Dict:
        """
        Calculate comprehensive performance metrics.
        
        Args:
            trade_results: DataFrame with trade results from strategy
            
        Returns:
            Dictionary with performance metrics
        """
        if trade_results.empty:
            return {}
            
        # Basic metrics
        total_trades = len(trade_results)
        winning_trades = len(trade_results[trade_results['net_return'] > 0])
        losing_trades = len(trade_results[trade_results['net_return'] < 0])
        
        # Returns analysis
        returns = trade_results['net_return']
        gross_returns = trade_results['gross_return']
        
        # Portfolio value over time
        final_value = trade_results['portfolio_value'].iloc[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # Calculate annualized metrics
        start_date = trade_results['buy_date'].min()
        end_date = trade_results['sell_date'].max()
        days_elapsed = (end_date - start_date).days
        years_elapsed = days_elapsed / 365.25
        
        annualized_return = (final_value / self.initial_capital) ** (1/years_elapsed) - 1 if years_elapsed > 0 else 0
        
        # Volatility (annualized)
        daily_returns = returns
        volatility = daily_returns.std() * np.sqrt(252)  # Assuming 252 trading days per year
        
        # Sharpe ratio
        excess_return = annualized_return - self.risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        # Drawdown analysis
        portfolio_values = trade_results['portfolio_value']
        running_max = portfolio_values.expanding().max()
        drawdowns = (portfolio_values - running_max) / running_max
        max_drawdown = drawdowns.min()
        
        # Calmar ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Win/Loss metrics
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        avg_win = returns[returns > 0].mean() if winning_trades > 0 else 0
        avg_loss = returns[returns < 0].mean() if losing_trades > 0 else 0
        
        profit_factor = abs(returns[returns > 0].sum() / returns[returns < 0].sum()) if losing_trades > 0 else float('inf')
        
        # Best and worst trades
        best_trade = returns.max()
        worst_trade = returns.min()
        
        # Monthly/yearly breakdown
        trade_results_copy = trade_results.copy()
        trade_results_copy['year'] = trade_results_copy['sell_date'].dt.year
        trade_results_copy['month'] = trade_results_copy['sell_date'].dt.month
        
        yearly_returns = trade_results_copy.groupby('year')['net_return'].sum()
        monthly_returns = trade_results_copy.groupby(['year', 'month'])['net_return'].sum()
        
        metrics = {
            # Basic Statistics
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            
            # Return Metrics
            'total_return': total_return,
            'annualized_return': annualized_return,
            'final_portfolio_value': final_value,
            
            # Risk Metrics
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            
            # Trade Analysis
            'avg_return_per_trade': returns.mean(),
            'avg_gross_return_per_trade': gross_returns.mean(),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            
            # Time Analysis
            'start_date': start_date,
            'end_date': end_date,
            'days_traded': days_elapsed,
            'years_traded': years_elapsed,
            
            # Breakdown
            'yearly_returns': yearly_returns.to_dict(),
            'monthly_returns': monthly_returns.to_dict(),
            
            # Transaction Costs Impact
            'gross_vs_net_impact': (gross_returns.mean() - returns.mean()),
        }
        
        return metrics
    
    def calculate_rolling_metrics(self, trade_results: pd.DataFrame, window: int = 30) -> pd.DataFrame:
        """
        Calculate rolling performance metrics.
        
        Args:
            trade_results: DataFrame with trade results
            window: Rolling window size in trades
            
        Returns:
            DataFrame with rolling metrics
        """
        if len(trade_results) < window:
            return pd.DataFrame()
            
        rolling_metrics = []
        
        for i in range(window - 1, len(trade_results)):
            window_data = trade_results.iloc[i-window+1:i+1]
            
            returns = window_data['net_return']
            portfolio_values = window_data['portfolio_value']
            
            # Calculate metrics for this window
            win_rate = (returns > 0).sum() / len(returns)
            avg_return = returns.mean()
            volatility = returns.std()
            
            # Drawdown for this window
            running_max = portfolio_values.expanding().max()
            drawdowns = (portfolio_values - running_max) / running_max
            max_dd = drawdowns.min()
            
            rolling_metrics.append({
                'trade_number': i + 1,
                'end_date': window_data['sell_date'].iloc[-1],
                'rolling_win_rate': win_rate,
                'rolling_avg_return': avg_return,
                'rolling_volatility': volatility,
                'rolling_max_drawdown': max_dd,
                'rolling_sharpe': (avg_return * np.sqrt(252)) / (volatility * np.sqrt(252)) if volatility > 0 else 0
            })
            
        return pd.DataFrame(rolling_metrics)
    
    def run_backtest(self, strategy_data: pd.DataFrame, strategy) -> Tuple[pd.DataFrame, Dict, pd.DataFrame]:
        """
        Run complete backtest analysis.
        
        Args:
            strategy_data: Raw strategy data with buy/sell prices
            strategy: Trading strategy instance
            
        Returns:
            Tuple of (trade_results, performance_metrics, rolling_metrics)
        """
        # Reset strategy
        strategy.reset()
        
        # Run strategy
        trade_results = strategy.run_strategy(strategy_data)
        
        if trade_results.empty:
            return pd.DataFrame(), {}, pd.DataFrame()
        
        # Calculate performance metrics
        performance_metrics = self.calculate_performance_metrics(trade_results)
        
        # Calculate rolling metrics
        rolling_metrics = self.calculate_rolling_metrics(trade_results, window=30)
        
        return trade_results, performance_metrics, rolling_metrics
    
    def print_performance_summary(self, metrics: Dict):
        """Print a formatted performance summary."""
        if not metrics:
            print("No performance metrics available.")
            return
            
        print("=" * 60)
        print("IBIT OVERNIGHT STRATEGY - BACKTEST RESULTS")
        print("=" * 60)
        
        print(f"\n📊 BASIC STATISTICS")
        print(f"Total Trades: {metrics['total_trades']:,}")
        print(f"Winning Trades: {metrics['winning_trades']:,}")
        print(f"Losing Trades: {metrics['losing_trades']:,}")
        print(f"Win Rate: {metrics['win_rate']:.1%}")
        
        print(f"\n💰 RETURN ANALYSIS")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Final Portfolio Value: ${metrics['final_portfolio_value']:,.2f}")
        print(f"Total Return: {metrics['total_return']:.1%}")
        print(f"Annualized Return: {metrics['annualized_return']:.1%}")
        print(f"Avg Return per Trade: {metrics['avg_return_per_trade']:.2%}")
        
        print(f"\n⚠️  RISK METRICS")
        print(f"Volatility (Annual): {metrics['volatility']:.1%}")
        print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"Maximum Drawdown: {metrics['max_drawdown']:.1%}")
        print(f"Calmar Ratio: {metrics['calmar_ratio']:.2f}")
        
        print(f"\n🎯 TRADE ANALYSIS")
        print(f"Best Trade: {metrics['best_trade']:.2%}")
        print(f"Worst Trade: {metrics['worst_trade']:.2%}")
        print(f"Average Win: {metrics['avg_win']:.2%}")
        print(f"Average Loss: {metrics['avg_loss']:.2%}")
        print(f"Profit Factor: {metrics['profit_factor']:.2f}")
        
        print(f"\n📅 TIME ANALYSIS")
        print(f"Start Date: {metrics['start_date'].strftime('%Y-%m-%d')}")
        print(f"End Date: {metrics['end_date'].strftime('%Y-%m-%d')}")
        print(f"Trading Period: {metrics['years_traded']:.2f} years")
        
        print(f"\n💸 COST ANALYSIS")
        print(f"Gross vs Net Impact: {metrics['gross_vs_net_impact']:.3%} per trade")
        print(f"Annual Cost Impact: {metrics['gross_vs_net_impact'] * 252:.1%}")
        
        print(f"\n📈 YEARLY PERFORMANCE")
        for year, ret in metrics['yearly_returns'].items():
            print(f"{year}: {ret:.1%}")
        
        print("=" * 60)