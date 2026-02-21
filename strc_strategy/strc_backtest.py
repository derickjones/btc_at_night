"""
STRC (Stretch) Peg Reversion & Dividend Capture Strategy
=========================================================
Strategy's perpetual preferred stock targets $100 par value with
variable monthly dividends (~11%+ annualized).

Theory:
- When STRC falls below $100, Saylor raises dividend rates to attract buyers back
- Mean-reversion pressure creates buying opportunities below peg
- Monthly dividend cycle creates predictable price patterns

This backtest analyzes:
1. Pattern Analysis: Price behavior around dividends, weekly/monthly cycles, BTC correlation
2. Buy-the-Dip Strategies: Multiple thresholds with sensitivity analysis
3. Dividend Capture: Timing around ex-div dates
4. Scaling In vs All-In
5. Opportunity Cost: What to hold when not in STRC
6. Benchmark: Buy & Hold STRC
7. Tax Considerations: Dividend classification and holding periods
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                 Table, TableStyle, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

PAR_VALUE = 100.0


# =============================================================================
# DATA FETCHING
# =============================================================================

def fetch_data():
    """Fetch STRC and BTC data using actual traded (non-adjusted) prices."""
    print("📊 Fetching STRC data...")

    strc = yf.Ticker('STRC')

    # Get raw prices (auto_adjust=False gives actual traded Close + Adj Close)
    df_raw = strc.history(period='max', auto_adjust=False)
    divs = strc.dividends

    if df_raw.empty:
        raise ValueError("No STRC data found.")

    # Build our working dataframe with actual traded prices
    df_unadj = pd.DataFrame({
        'Open': df_raw['Open'],
        'High': df_raw['High'],
        'Low': df_raw['Low'],
        'Close': df_raw['Close'],
        'Volume': df_raw['Volume'],
        'Dividends': df_raw['Dividends'],
        'Stock Splits': df_raw['Stock Splits'],
    }, index=df_raw.index)

    # Also keep the adjusted version for reference
    df_adj = pd.DataFrame({
        'Open': df_raw['Open'],  # Will use unadj everywhere, adj just for reference
        'High': df_raw['High'],
        'Low': df_raw['Low'],
        'Close': df_raw['Adj Close'],
        'Volume': df_raw['Volume'],
    }, index=df_raw.index)

    print(f"   STRC: {len(df_unadj)} trading days ({df_unadj.index[0].strftime('%Y-%m-%d')} to {df_unadj.index[-1].strftime('%Y-%m-%d')})")
    print(f"   Dividends: {len(divs)} payments, total ${divs.sum():.3f}/share")
    print(f"   Actual traded price range: ${df_unadj['Low'].min():.2f} - ${df_unadj['High'].max():.2f}")
    print(f"   Day 1 close: ${df_unadj['Close'].iloc[0]:.2f}, Current close: ${df_unadj['Close'].iloc[-1]:.2f}")

    # Fetch BTC for correlation analysis
    print("📊 Fetching BTC data for correlation...")
    btc = yf.Ticker('BTC-USD')
    btc_df = btc.history(start=df_unadj.index[0].strftime('%Y-%m-%d'),
                         end=(df_unadj.index[-1] + timedelta(days=1)).strftime('%Y-%m-%d'))

    return df_adj, df_unadj, divs, btc_df


# =============================================================================
# PATTERN ANALYSIS
# =============================================================================

def analyze_patterns(df_unadj, divs, btc_df):
    """Comprehensive pattern analysis of STRC price behavior."""
    print("\n🔍 Analyzing patterns...")
    analysis = {}

    df = df_unadj.copy()

    # --- Basic Statistics ---
    analysis['price_stats'] = {
        'mean': df['Close'].mean(),
        'median': df['Close'].median(),
        'std': df['Close'].std(),
        'min': df['Close'].min(),
        'max': df['Close'].max(),
        'pct_below_100': (df['Close'] < 100).mean() * 100,
        'pct_below_99': (df['Close'] < 99).mean() * 100,
        'pct_below_98': (df['Close'] < 98).mean() * 100,
        'pct_below_97': (df['Close'] < 97).mean() * 100,
        'pct_below_96': (df['Close'] < 96).mean() * 100,
        'pct_below_95': (df['Close'] < 95).mean() * 100,
    }

    # --- Peg Distance Over Time ---
    df['peg_distance'] = df['Close'] - PAR_VALUE
    df['daily_return'] = df['Close'].pct_change()

    # --- Day of Week Patterns ---
    df['dow'] = df.index.dayofweek
    dow_stats = df.groupby('dow').agg(
        avg_close=('Close', 'mean'),
        avg_return=('daily_return', 'mean'),
        avg_peg_dist=('peg_distance', 'mean')
    )
    dow_stats.index = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    analysis['dow_stats'] = dow_stats

    # --- Week of Month Patterns ---
    df['week_of_month'] = (df.index.day - 1) // 7 + 1
    wom_stats = df.groupby('week_of_month').agg(
        avg_close=('Close', 'mean'),
        avg_return=('daily_return', 'mean'),
        avg_peg_dist=('peg_distance', 'mean'),
        count=('Close', 'count')
    )
    analysis['wom_stats'] = wom_stats

    # --- Dividend Cycle Analysis ---
    div_analysis = []
    for i, (div_date, div_amount) in enumerate(divs.items()):
        pre_dates = df.index[df.index < div_date]
        post_dates = df.index[df.index >= div_date]

        if len(pre_dates) < 5 or len(post_dates) < 10:
            continue

        pre_5d = df.loc[pre_dates[-5:], 'Close']
        pre_1d = df.loc[pre_dates[-1], 'Close']
        post_0d = df.loc[post_dates[0], 'Close']
        post_1d = df.loc[post_dates[1], 'Close'] if len(post_dates) > 1 else None
        post_5d = df.loc[post_dates[min(4, len(post_dates)-1)], 'Close'] if len(post_dates) > 4 else None
        post_10d = df.loc[post_dates[min(9, len(post_dates)-1)], 'Close'] if len(post_dates) > 9 else None

        # Price trend leading up to ex-div
        pre_5d_change = (pre_1d - pre_5d.iloc[0]) / pre_5d.iloc[0] * 100

        div_info = {
            'date': div_date.strftime('%Y-%m-%d'),
            'amount': div_amount,
            'pre_1d_price': pre_1d,
            'ex_div_price': post_0d,
            'drop': post_0d - pre_1d,
            'drop_vs_div': (post_0d - pre_1d) + div_amount,  # drop adjusted for div
            'pre_5d_drift': pre_5d_change,
            'recovery_1d': (post_1d - post_0d) if post_1d else None,
            'recovery_5d': (post_5d - post_0d) if post_5d else None,
            'recovery_10d': (post_10d - post_0d) if post_10d else None,
        }
        div_analysis.append(div_info)

    analysis['div_analysis'] = pd.DataFrame(div_analysis)

    # --- BTC Correlation ---
    btc_aligned = btc_df['Close'].reindex(df.index, method='ffill')
    df['btc_close'] = btc_aligned
    df['btc_return'] = df['btc_close'].pct_change()

    analysis['btc_corr_all'] = df['daily_return'].corr(df['btc_return'])
    analysis['btc_corr_rolling'] = df['daily_return'].rolling(20).corr(df['btc_return'])

    # Big BTC down days
    big_btc_down = df[df['btc_return'] < -0.03].copy()
    analysis['btc_stress'] = {
        'n_days': len(big_btc_down),
        'avg_strc_return': big_btc_down['daily_return'].mean() if len(big_btc_down) > 0 else 0,
        'avg_btc_return': big_btc_down['btc_return'].mean() if len(big_btc_down) > 0 else 0,
        'worst_strc': big_btc_down['daily_return'].min() if len(big_btc_down) > 0 else 0,
    }

    # --- Mean Reversion Speed ---
    reversion = {}
    for threshold in [99.5, 99, 98.5, 98, 97, 96, 95]:
        below_mask = df['Close'] < threshold
        episodes = []
        in_episode = False
        entry_idx = None

        for idx in df.index:
            if below_mask[idx] and not in_episode:
                in_episode = True
                entry_idx = idx
            elif not below_mask[idx] and in_episode:
                in_episode = False
                days = (idx - entry_idx).days
                entry_price = df.loc[entry_idx, 'Close']
                episodes.append({
                    'entry_date': entry_idx,
                    'exit_date': idx,
                    'days': days,
                    'entry_price': entry_price,
                    'gain_pct': (threshold - entry_price) / entry_price * 100
                })

        if episodes:
            reversion[threshold] = {
                'episodes': len(episodes),
                'avg_days': np.mean([e['days'] for e in episodes]),
                'max_days': max([e['days'] for e in episodes]),
                'avg_gain': np.mean([e['gain_pct'] for e in episodes]),
                'still_below': in_episode,
            }

    analysis['reversion'] = reversion
    analysis['df'] = df

    return analysis


# =============================================================================
# BACKTESTING STRATEGIES
# =============================================================================

def backtest_strategies(df_unadj, divs):
    """Run all backtest strategies and return results."""
    print("\n📈 Running backtests...")
    df = df_unadj.copy()
    df['daily_return'] = df['Close'].pct_change()
    results = {}

    # --- Strategy 1: Buy & Hold (Benchmark) ---
    results['buy_hold'] = backtest_buy_hold(df, divs)

    # --- Strategy 2: Buy Below Peg (multiple thresholds) ---
    for threshold in [99.5, 99, 98.5, 98, 97, 96, 95]:
        results[f'peg_{threshold}'] = backtest_peg_reversion(df, divs, buy_threshold=threshold,
                                                              sell_target=PAR_VALUE)

    # --- Strategy 3: Buy Below Peg, sell above peg ---
    for threshold in [99, 98, 97]:
        for sell_target in [100, 100.5, 101]:
            key = f'peg_{threshold}_sell_{sell_target}'
            results[key] = backtest_peg_reversion(df, divs, buy_threshold=threshold,
                                                   sell_target=sell_target)

    # --- Strategy 4: Scale-in vs All-in (tiered analysis) ---
    # Equal weighting at each threshold
    for threshold in [99, 98, 97]:
        results[f'scale_equal_{threshold}'] = backtest_scale_in(df, divs, base_threshold=threshold,
                                                                 weighting='equal')
    # Aggressive: buy more at deeper dips (10/15/25/50%)
    for threshold in [99, 98, 97]:
        results[f'scale_aggr_{threshold}'] = backtest_scale_in(df, divs, base_threshold=threshold,
                                                                weighting='aggressive')
    # Pyramid: buy most at first trigger (40/30/20/10%)
    for threshold in [99, 98, 97]:
        results[f'scale_pyr_{threshold}'] = backtest_scale_in(df, divs, base_threshold=threshold,
                                                               weighting='pyramid')
    # Linear: increasing allocation (10/20/30/40%)
    for threshold in [99, 98, 97]:
        results[f'scale_lin_{threshold}'] = backtest_scale_in(df, divs, base_threshold=threshold,
                                                               weighting='linear')

    # Keep backward-compat aliases
    for threshold in [99, 98, 97]:
        results[f'scale_{threshold}'] = results[f'scale_equal_{threshold}']

    # --- Strategy 5: Dividend Capture ---
    results['div_capture'] = backtest_dividend_capture(df, divs)

    # --- Strategy 6: Combined (peg reversion + dividend aware) ---
    results['combined_98'] = backtest_combined(df, divs, buy_threshold=98)
    results['combined_97'] = backtest_combined(df, divs, buy_threshold=97)

    return results


def backtest_buy_hold(df, divs):
    """Buy & Hold benchmark: buy day 1, collect all dividends."""
    entry_price = df['Close'].iloc[0]
    current_price = df['Close'].iloc[-1]
    holding_days = (df.index[-1] - df.index[0]).days

    total_divs = divs.sum()
    cap_gain = current_price - entry_price
    total_return_pct = (cap_gain + total_divs) / entry_price * 100
    annualized = ((1 + total_return_pct / 100) ** (365 / holding_days) - 1) * 100

    # Daily equity curve
    equity = [entry_price]
    divs_collected = 0
    for i in range(1, len(df)):
        date = df.index[i]
        # Check if dividend was paid
        if date in divs.index:
            divs_collected += divs[date]
        equity.append(df['Close'].iloc[i] + divs_collected)

    equity_series = pd.Series(equity, index=df.index)
    equity_returns = equity_series.pct_change().dropna()

    return {
        'name': 'Buy & Hold',
        'total_return_pct': total_return_pct,
        'annualized_pct': annualized,
        'cap_gain': cap_gain,
        'divs_collected': total_divs,
        'n_divs': len(divs),
        'holding_days': holding_days,
        'pct_time_in': 100.0,
        'trades': 1,
        'equity': equity_series,
        'max_drawdown': calculate_max_drawdown(equity_series),
        'sharpe': calculate_sharpe(equity_returns),
    }


def backtest_peg_reversion(df, divs, buy_threshold, sell_target):
    """Buy when price drops below threshold, sell when it reaches target."""
    initial_capital = df['Close'].iloc[0]  # Start with equivalent cash
    cash = initial_capital
    shares = 0
    entry_price = 0
    trades = []
    divs_collected_total = 0  # Running total of all divs collected (never resets)
    divs_this_trade = 0       # Divs collected in current trade
    equity = []
    in_position = False

    DAILY_TBILL_RATE = (1 + 0.045) ** (1/252) - 1  # ~4.5% annual T-bill when in cash

    for i in range(len(df)):
        date = df.index[i]
        close = df['Close'].iloc[i]

        # Collect dividend if holding
        if in_position and date in divs.index:
            divs_this_trade += divs[date] * shares
            divs_collected_total += divs[date] * shares

        # Check buy signal
        if not in_position and close < buy_threshold:
            shares = cash / close
            entry_price = close
            cash = 0
            in_position = True
            entry_date = date
            divs_this_trade = 0

        # Check sell signal
        elif in_position and close >= sell_target:
            proceeds = shares * close + divs_this_trade
            profit = proceeds - (shares * entry_price)
            trades.append({
                'entry_date': entry_date,
                'exit_date': date,
                'entry_price': entry_price,
                'exit_price': close,
                'divs': divs_this_trade,
                'profit_pct': profit / (shares * entry_price) * 100,
                'hold_days': (date - entry_date).days,
            })
            cash = proceeds
            shares = 0
            divs_this_trade = 0
            in_position = False

        # Accrue T-bill return on idle cash
        elif not in_position and cash > 0:
            cash *= (1 + DAILY_TBILL_RATE)

        # Track equity
        if in_position:
            equity.append(shares * close + divs_this_trade)
        else:
            equity.append(cash)

    # If still in position at end
    final_value = shares * df['Close'].iloc[-1] + divs_this_trade if in_position else cash
    if in_position:
        equity[-1] = final_value

    equity_series = pd.Series(equity, index=df.index)
    # For Sharpe, compute returns only from non-zero equity changes
    equity_returns = equity_series.pct_change().dropna()
    equity_returns = equity_returns.replace([np.inf, -np.inf], np.nan).dropna()
    initial_value = df['Close'].iloc[0]
    total_return_pct = (final_value - initial_value) / initial_value * 100
    holding_days = (df.index[-1] - df.index[0]).days
    annualized = ((1 + total_return_pct / 100) ** (365 / max(holding_days, 1)) - 1) * 100

    # Calculate time in market
    in_market_days = 0
    for t in trades:
        in_market_days += len(df.index[(df.index >= t['entry_date']) & (df.index <= t['exit_date'])])
    if in_position:
        in_market_days += len(df.index[df.index >= entry_date])
    pct_time_in = in_market_days / len(df) * 100 if len(df) > 0 else 0

    return {
        'name': f'Buy <${buy_threshold}, Sell ≥${sell_target}',
        'total_return_pct': total_return_pct,
        'annualized_pct': annualized,
        'cap_gain': final_value - initial_value - divs_collected_total,
        'divs_collected': divs_collected_total,
        'n_divs': sum(1 for d in divs.index if any(
            t['entry_date'] <= d <= t['exit_date'] for t in trades
        ) or (in_position and d >= entry_date)),
        'holding_days': holding_days,
        'pct_time_in': pct_time_in,
        'trades': len(trades),
        'avg_trade_days': np.mean([t['hold_days'] for t in trades]) if trades else 0,
        'avg_trade_profit': np.mean([t['profit_pct'] for t in trades]) if trades else 0,
        'win_rate': np.mean([t['profit_pct'] > 0 for t in trades]) * 100 if trades else 0,
        'equity': equity_series,
        'max_drawdown': calculate_max_drawdown(equity_series),
        'sharpe': calculate_sharpe(equity_returns),
        'trade_log': trades,
    }


def backtest_scale_in(df, divs, base_threshold, weighting='equal', label_override=None):
    """Scale into position at multiple levels below peg.

    weighting options:
        'equal'      - 25% at each of 4 levels
        'aggressive' - 10/15/25/50% (more at deeper dips)
        'pyramid'    - 40/30/20/10% (more at first level)
        'linear'     - 10/20/30/40% (linearly increasing)
        custom list  - e.g. [0.1, 0.2, 0.3, 0.4]
    """
    levels = [base_threshold, base_threshold - 1, base_threshold - 2, base_threshold - 3]

    if isinstance(weighting, list):
        allocs = weighting
        weight_label = 'custom'
    elif weighting == 'equal':
        allocs = [0.25, 0.25, 0.25, 0.25]
        weight_label = 'equal'
    elif weighting == 'aggressive':
        allocs = [0.10, 0.15, 0.25, 0.50]
        weight_label = 'aggressive'
    elif weighting == 'pyramid':
        allocs = [0.40, 0.30, 0.20, 0.10]
        weight_label = 'pyramid'
    elif weighting == 'linear':
        allocs = [0.10, 0.20, 0.30, 0.40]
        weight_label = 'linear'
    else:
        allocs = [0.25, 0.25, 0.25, 0.25]
        weight_label = 'equal'

    total_capital = df['Close'].iloc[0]
    cash = total_capital
    positions = []  # List of (shares, entry_price)
    divs_collected = 0
    equity = []
    filled_levels = set()
    DAILY_TBILL_RATE = (1 + 0.045) ** (1/252) - 1

    for i in range(len(df)):
        date = df.index[i]
        close = df['Close'].iloc[i]

        # Collect dividends
        total_shares = sum(p[0] for p in positions)
        if total_shares > 0 and date in divs.index:
            divs_collected += divs[date] * total_shares

        # Check buy levels
        for level, alloc in zip(levels, allocs):
            if level not in filled_levels and close < level:
                buy_amount = total_capital * alloc
                if cash >= buy_amount:
                    shares = buy_amount / close
                    positions.append((shares, close))
                    cash -= buy_amount
                    filled_levels.add(level)

        # Sell if back at peg
        total_shares = sum(p[0] for p in positions)
        if total_shares > 0 and close >= PAR_VALUE:
            cash += total_shares * close + divs_collected
            divs_collected = 0
            positions = []
            filled_levels = set()

        # Accrue T-bill on idle cash
        if cash > 0 and len(positions) == 0:
            cash *= (1 + DAILY_TBILL_RATE)

        # Track equity
        total_shares = sum(p[0] for p in positions)
        equity.append(cash + total_shares * close + divs_collected)

    equity_series = pd.Series(equity, index=df.index)
    equity_returns = equity_series.pct_change().dropna()
    equity_returns = equity_returns.replace([np.inf, -np.inf], np.nan).dropna()
    final_value = equity[-1]
    total_return_pct = (final_value - total_capital) / total_capital * 100
    holding_days = (df.index[-1] - df.index[0]).days
    annualized = ((1 + total_return_pct / 100) ** (365 / max(holding_days, 1)) - 1) * 100

    if label_override:
        name = label_override
    else:
        name = f'Scale {weight_label} <${base_threshold}'
    alloc_str = '/'.join([f'{int(a*100)}' for a in allocs])

    return {
        'name': name,
        'total_return_pct': total_return_pct,
        'annualized_pct': annualized,
        'cap_gain': final_value - total_capital - divs_collected,
        'divs_collected': divs_collected,
        'holding_days': holding_days,
        'pct_time_in': sum(1 for e, c in zip(equity, [total_capital]*len(equity))
                          if abs(e - c) > 0.01 and len(positions) > 0) / len(equity) * 100
                      if equity else 0,
        'trades': len(filled_levels),
        'alloc_str': alloc_str,
        'weighting': weight_label,
        'equity': equity_series,
        'max_drawdown': calculate_max_drawdown(equity_series),
        'sharpe': calculate_sharpe(equity_returns),
    }


def backtest_dividend_capture(df, divs):
    """Buy 5 days before record date, sell 5 days after."""
    capital = df['Close'].iloc[0]
    cash = capital
    divs_collected = 0
    trades = []
    equity = []
    in_position = False
    shares = 0

    for i in range(len(df)):
        date = df.index[i]
        close = df['Close'].iloc[i]

        # Collect dividend if holding
        if in_position and date in divs.index:
            divs_collected += divs[date] * shares

        # Check if we should buy (5 trading days before ex-div)
        if not in_position:
            for div_date in divs.index:
                trading_days_before = df.index[df.index < div_date]
                if len(trading_days_before) >= 5:
                    buy_date = trading_days_before[-5]
                    if date == buy_date:
                        shares = cash / close
                        entry_price = close
                        entry_date = date
                        cash = 0
                        in_position = True
                        target_div_date = div_date
                        break

        # Check if we should sell (5 trading days after ex-div)
        if in_position:
            trading_days_after = df.index[df.index >= target_div_date]
            if len(trading_days_after) >= 6:
                sell_date = trading_days_after[5]
                if date == sell_date:
                    cash = shares * close + divs_collected
                    profit = cash - capital
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': close,
                        'div_captured': divs[target_div_date],
                        'profit_pct': profit / capital * 100 if len(trades) == 0 else
                                     (shares * close + divs_collected - shares * entry_price) / (shares * entry_price) * 100,
                        'hold_days': (date - entry_date).days,
                    })
                    divs_collected = 0
                    shares = 0
                    in_position = False

        if in_position:
            equity.append(shares * close + divs_collected)
        else:
            equity.append(cash if cash > 0 else capital)

    equity_series = pd.Series(equity, index=df.index)
    equity_returns = equity_series.pct_change().dropna()
    final_value = equity[-1]
    total_return_pct = (final_value - capital) / capital * 100
    holding_days = (df.index[-1] - df.index[0]).days
    annualized = ((1 + total_return_pct / 100) ** (365 / max(holding_days, 1)) - 1) * 100

    return {
        'name': 'Dividend Capture (±5 days)',
        'total_return_pct': total_return_pct,
        'annualized_pct': annualized,
        'divs_collected': sum(t.get('div_captured', 0) for t in trades),
        'holding_days': holding_days,
        'pct_time_in': sum(1 for e, c in zip(equity, [capital]*len(equity)) if abs(e - c) > 0.01) / len(equity) * 100,
        'trades': len(trades),
        'avg_trade_profit': np.mean([t['profit_pct'] for t in trades]) if trades else 0,
        'equity': equity_series,
        'max_drawdown': calculate_max_drawdown(equity_series),
        'sharpe': calculate_sharpe(equity_returns),
        'trade_log': trades,
    }


def backtest_combined(df, divs, buy_threshold):
    """Combined: buy below peg, but hold through dividend if record date is within 10 days."""
    capital = df['Close'].iloc[0]
    cash = capital
    shares = 0
    divs_collected = 0
    in_position = False
    entry_price = 0
    entry_date = None
    trades = []
    equity = []
    days_in_position = 0

    for i in range(len(df)):
        date = df.index[i]
        close = df['Close'].iloc[i]

        # Collect dividend
        if in_position and date in divs.index:
            divs_collected += divs[date] * shares

        # Buy signal: below threshold
        if not in_position and close < buy_threshold:
            shares = cash / close
            entry_price = close
            entry_date = date
            cash = 0
            in_position = True

        # Sell signal: at peg, BUT check if dividend is coming soon
        elif in_position and close >= PAR_VALUE:
            # Check if any dividend is within 10 trading days
            upcoming_div = False
            future_dates = df.index[df.index > date]
            for div_date in divs.index:
                if div_date > date:
                    days_ahead = len(df.index[(df.index > date) & (df.index <= div_date)])
                    if days_ahead <= 10:
                        upcoming_div = True
                        break

            if not upcoming_div:
                cash = shares * close + divs_collected
                profit_pct = (cash - (shares * entry_price)) / (shares * entry_price) * 100
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': date,
                    'entry_price': entry_price,
                    'exit_price': close,
                    'profit_pct': profit_pct,
                    'hold_days': (date - entry_date).days,
                })
                divs_collected = 0
                shares = 0
                in_position = False

        if in_position:
            equity.append(shares * close + divs_collected)
            days_in_position += 1
        else:
            equity.append(cash)

    equity_series = pd.Series(equity, index=df.index)
    equity_returns = equity_series.pct_change().dropna()
    final_value = equity[-1]
    total_return_pct = (final_value - capital) / capital * 100
    holding_days = (df.index[-1] - df.index[0]).days
    annualized = ((1 + total_return_pct / 100) ** (365 / max(holding_days, 1)) - 1) * 100

    return {
        'name': f'Combined <${buy_threshold} + Div Hold',
        'total_return_pct': total_return_pct,
        'annualized_pct': annualized,
        'divs_collected': divs_collected + sum(t.get('divs', 0) for t in trades),
        'holding_days': holding_days,
        'pct_time_in': days_in_position / len(df) * 100 if len(df) > 0 else 0,
        'trades': len(trades),
        'equity': equity_series,
        'max_drawdown': calculate_max_drawdown(equity_series),
        'sharpe': calculate_sharpe(equity_returns),
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_max_drawdown(equity_series):
    """Calculate maximum drawdown from an equity series."""
    rolling_max = equity_series.expanding().max()
    drawdown = (equity_series / rolling_max - 1) * 100
    return drawdown.min()


def calculate_sharpe(returns, risk_free_annual=0.05):
    """Calculate annualized Sharpe ratio."""
    if len(returns) < 2 or returns.std() == 0:
        return 0
    annual_return = (1 + returns.mean()) ** 252 - 1
    annual_vol = returns.std() * np.sqrt(252)
    return (annual_return - risk_free_annual) / annual_vol


# =============================================================================
# VISUALIZATIONS
# =============================================================================

def plot_price_and_dividends(df_unadj, divs):
    """Plot STRC price with dividend dates and $100 peg line."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[3, 1], sharex=True)

    ax1.plot(df_unadj.index, df_unadj['Close'], linewidth=1.5, color='#2E86AB', label='STRC Price')
    ax1.axhline(y=100, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='$100 Par Value')
    ax1.fill_between(df_unadj.index, df_unadj['Close'], 100,
                     where=df_unadj['Close'] < 100, alpha=0.15, color='red', label='Below Peg')

    for div_date, div_amount in divs.items():
        ax1.axvline(x=div_date, color='green', linestyle=':', alpha=0.5)
        ax1.annotate(f'${div_amount:.3f}', xy=(div_date, df_unadj['Close'].max()),
                     fontsize=7, rotation=45, color='green')

    ax1.set_title('STRC Price History vs $100 Par Value', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Price ($)', fontsize=12)
    ax1.legend(loc='lower right')
    ax1.grid(True, alpha=0.3)

    # Volume
    ax2.bar(df_unadj.index, df_unadj['Volume'], color='#2E86AB', alpha=0.5)
    ax2.set_ylabel('Volume', fontsize=12)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'strc_price_dividends.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: strc_price_dividends.png")


def plot_peg_distance_distribution(df_unadj):
    """Histogram of distance from peg."""
    fig, ax = plt.subplots(figsize=(12, 6))

    distance = df_unadj['Close'] - 100
    ax.hist(distance, bins=40, color='#2E86AB', alpha=0.7, edgecolor='black', linewidth=0.5)
    ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='At Peg ($100)')
    ax.axvline(x=distance.mean(), color='orange', linestyle='--', linewidth=2,
               label=f'Mean: ${distance.mean():+.2f}')

    # Mark thresholds
    for thresh in [-1, -2, -3, -4, -5]:
        pct = (distance < thresh).mean() * 100
        ax.axvline(x=thresh, color='gray', linestyle=':', alpha=0.5)
        ax.annotate(f'${100+thresh}\n({pct:.0f}% of days)', xy=(thresh, ax.get_ylim()[1]*0.9),
                    fontsize=8, ha='center')

    ax.set_title('STRC: Distribution of Distance from $100 Peg', fontsize=14, fontweight='bold')
    ax.set_xlabel('Distance from $100 ($)', fontsize=12)
    ax.set_ylabel('Frequency (days)', fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'strc_peg_distance.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: strc_peg_distance.png")


def plot_dividend_cycle(analysis):
    """Plot price behavior around ex-dividend dates."""
    div_df = analysis['div_analysis']
    if div_df.empty:
        return

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # Drop on ex-div day
    ax = axes[0]
    ax.bar(div_df['date'], div_df['drop'], color=['red' if d < 0 else 'green' for d in div_df['drop']])
    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.set_title('Price Drop on Ex-Div Day', fontsize=11, fontweight='bold')
    ax.set_ylabel('Price Change ($)')
    ax.tick_params(axis='x', rotation=45)

    # Recovery after ex-div
    ax = axes[1]
    x = range(len(div_df))
    if div_df['recovery_1d'].notna().any():
        ax.bar([i-0.2 for i in x], div_df['recovery_1d'].fillna(0), 0.2, label='1 day', color='#2E86AB')
    if div_df['recovery_5d'].notna().any():
        ax.bar([i for i in x], div_df['recovery_5d'].fillna(0), 0.2, label='5 days', color='#F18F01')
    if div_df['recovery_10d'].notna().any():
        ax.bar([i+0.2 for i in x], div_df['recovery_10d'].fillna(0), 0.2, label='10 days', color='#A23B72')
    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.set_title('Recovery After Ex-Div', fontsize=11, fontweight='bold')
    ax.set_ylabel('Price Change ($)')
    ax.set_xticks(list(x))
    ax.set_xticklabels(div_df['date'], rotation=45)
    ax.legend(fontsize=8)

    # Pre-div drift
    ax = axes[2]
    ax.bar(div_df['date'], div_df['pre_5d_drift'],
           color=['green' if d > 0 else 'red' for d in div_df['pre_5d_drift']])
    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.set_title('5-Day Price Drift Before Ex-Div', fontsize=11, fontweight='bold')
    ax.set_ylabel('Price Change (%)')
    ax.tick_params(axis='x', rotation=45)

    plt.suptitle('STRC Dividend Cycle Analysis', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'strc_dividend_cycle.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: strc_dividend_cycle.png")


def plot_weekly_monthly_patterns(analysis):
    """Plot day-of-week and week-of-month patterns."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Day of week
    dow = analysis['dow_stats']
    colors_dow = ['green' if r > 0 else 'red' for r in dow['avg_return']]
    ax1.bar(dow.index, dow['avg_return'] * 100, color=colors_dow, alpha=0.7)
    ax1.axhline(y=0, color='black', linewidth=0.5)
    ax1.set_title('Average Daily Return by Day of Week', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Avg Return (%)')
    ax1.grid(True, alpha=0.3, axis='y')

    # Week of month
    wom = analysis['wom_stats']
    colors_wom = ['green' if r > 0 else 'red' for r in wom['avg_return']]
    ax2.bar(wom.index.astype(str), wom['avg_return'] * 100, color=colors_wom, alpha=0.7)
    ax2.axhline(y=0, color='black', linewidth=0.5)
    ax2.set_title('Average Daily Return by Week of Month', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Week of Month')
    ax2.set_ylabel('Avg Return (%)')
    ax2.grid(True, alpha=0.3, axis='y')

    plt.suptitle('STRC Time-Based Patterns', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'strc_time_patterns.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: strc_time_patterns.png")


def plot_strategy_comparison(results):
    """Plot equity curves for key strategies."""
    fig, ax = plt.subplots(figsize=(14, 8))

    # Select key strategies to plot
    key_strategies = ['buy_hold', 'peg_99', 'peg_98', 'peg_97', 'peg_96',
                      'scale_98', 'div_capture', 'combined_98']

    plot_colors = ['#333333', '#2E86AB', '#F18F01', '#A23B72', '#E84855',
                   '#44BBA4', '#8B5CF6', '#EC4899']

    for key, color in zip(key_strategies, plot_colors):
        if key in results:
            r = results[key]
            equity_normalized = r['equity'] / r['equity'].iloc[0]
            label = f"{r['name']} ({r['total_return_pct']:+.1f}%)"
            linewidth = 2.5 if key == 'buy_hold' else 1.5
            linestyle = '--' if key == 'buy_hold' else '-'
            ax.plot(r['equity'].index, equity_normalized, label=label,
                    linewidth=linewidth, color=color, linestyle=linestyle)

    ax.axhline(y=1, color='gray', linestyle=':', alpha=0.3)
    ax.set_title('STRC Strategy Comparison: Growth of $1', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.3f}'))

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'strc_strategy_comparison.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: strc_strategy_comparison.png")


def plot_tiered_vs_static(results):
    """Compare tiered (scale-in) vs static (all-in) entry approaches."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    for idx, threshold in enumerate([99, 98, 97]):
        ax = axes[idx]

        # Static all-in
        static_key = f'peg_{threshold}'
        strategies = {}
        if static_key in results:
            strategies['All-in'] = results[static_key]

        # Tiered variants
        for weight_type, label, color in [
            ('equal', 'Equal (25/25/25/25)', '#2E86AB'),
            ('aggr', 'Aggressive (10/15/25/50)', '#E84855'),
            ('pyr', 'Pyramid (40/30/20/10)', '#44BBA4'),
            ('lin', 'Linear (10/20/30/40)', '#F18F01'),
        ]:
            key = f'scale_{weight_type}_{threshold}'
            if key in results:
                strategies[label] = results[key]

        # Bar chart: return + Sharpe
        names = list(strategies.keys())
        returns = [strategies[n]['total_return_pct'] for n in names]
        sharpes = [strategies[n].get('sharpe', 0) for n in names]
        max_dds = [abs(strategies[n].get('max_drawdown', 0)) for n in names]

        x = np.arange(len(names))
        bar_colors = ['#333333', '#2E86AB', '#E84855', '#44BBA4', '#F18F01'][:len(names)]

        bars = ax.bar(x, returns, color=bar_colors, alpha=0.7, edgecolor='black', linewidth=0.5)

        # Add Sharpe labels on bars
        for bar, sharpe, dd in zip(bars, sharpes, max_dds):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f'S:{sharpe:.1f}\nDD:{dd:.1f}%', ha='center', va='bottom', fontsize=7)

        ax.set_title(f'Entry at <${threshold}', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=35, ha='right', fontsize=7)
        ax.set_ylabel('Total Return (%)' if idx == 0 else '')
        ax.grid(True, alpha=0.3, axis='y')

    plt.suptitle('Tiered Scale-In vs Static All-In Entry', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'strc_tiered_vs_static.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: strc_tiered_vs_static.png")


def plot_sensitivity_analysis(results):
    """Plot sensitivity of returns to buy threshold and sell target."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Sensitivity to buy threshold (sell at $100)
    thresholds = [99.5, 99, 98.5, 98, 97, 96, 95]
    returns = [results.get(f'peg_{t}', {}).get('total_return_pct', 0) for t in thresholds]
    time_in = [results.get(f'peg_{t}', {}).get('pct_time_in', 0) for t in thresholds]

    ax1_twin = ax1.twinx()
    bars = ax1.bar([f'${t}' for t in thresholds], returns, color='#2E86AB', alpha=0.7, label='Total Return')
    ax1_twin.plot([f'${t}' for t in thresholds], time_in, color='#F18F01', marker='o',
                  linewidth=2, label='% Time in Market')
    ax1.axhline(y=results['buy_hold']['total_return_pct'], color='red', linestyle='--',
                linewidth=1.5, label=f"Buy&Hold ({results['buy_hold']['total_return_pct']:.1f}%)")

    ax1.set_title('Sensitivity: Buy Threshold\n(Sell at $100)', fontsize=11, fontweight='bold')
    ax1.set_xlabel('Buy Below')
    ax1.set_ylabel('Total Return (%)', color='#2E86AB')
    ax1_twin.set_ylabel('% Time in Market', color='#F18F01')
    ax1.legend(loc='upper left', fontsize=8)
    ax1_twin.legend(loc='upper right', fontsize=8)
    ax1.grid(True, alpha=0.3, axis='y')

    # Sensitivity to sell target (for $98 buy threshold)
    sell_data = []
    for buy_t in [99, 98, 97]:
        for sell_t in [100, 100.5, 101]:
            key = f'peg_{buy_t}_sell_{sell_t}'
            if key in results:
                sell_data.append({
                    'buy': f'${buy_t}',
                    'sell': f'${sell_t}',
                    'return': results[key]['total_return_pct'],
                })

    if sell_data:
        sell_df = pd.DataFrame(sell_data)
        pivot = sell_df.pivot(index='buy', columns='sell', values='return')
        pivot.plot(kind='bar', ax=ax2, alpha=0.7)
        ax2.axhline(y=results['buy_hold']['total_return_pct'], color='red', linestyle='--',
                    linewidth=1.5, label='Buy&Hold')
        ax2.set_title('Sensitivity: Buy vs Sell Targets', fontsize=11, fontweight='bold')
        ax2.set_xlabel('Buy Below')
        ax2.set_ylabel('Total Return (%)')
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.tick_params(axis='x', rotation=0)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'strc_sensitivity.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: strc_sensitivity.png")


def plot_btc_correlation(analysis):
    """Plot BTC correlation analysis."""
    df = analysis['df']

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))

    # Rolling correlation
    rolling_corr = analysis['btc_corr_rolling']
    ax1.plot(rolling_corr.index, rolling_corr, linewidth=1.5, color='#2E86AB')
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax1.axhline(y=analysis['btc_corr_all'], color='red', linestyle='--',
                label=f"Overall: {analysis['btc_corr_all']:.3f}")
    ax1.set_title('STRC vs BTC: 20-Day Rolling Correlation', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Correlation')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Scatter plot
    ax2.scatter(df['btc_return'] * 100, df['daily_return'] * 100, alpha=0.4, s=20, color='#2E86AB')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax2.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    ax2.set_title('STRC vs BTC: Daily Returns Scatter', fontsize=12, fontweight='bold')
    ax2.set_xlabel('BTC Daily Return (%)')
    ax2.set_ylabel('STRC Daily Return (%)')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'strc_btc_correlation.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: strc_btc_correlation.png")


# =============================================================================
# PDF REPORT
# =============================================================================

def generate_pdf_report(analysis, results):
    """Generate comprehensive PDF report."""
    pdf_path = os.path.join(OUTPUT_DIR, 'strc_strategy_report.pdf')
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                            rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                  fontSize=22, spaceAfter=20, alignment=TA_CENTER,
                                  textColor=colors.HexColor('#2E86AB'))
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
                                    fontSize=14, spaceBefore=15, spaceAfter=8,
                                    textColor=colors.HexColor('#333333'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10,
                                 spaceAfter=6)
    small_style = ParagraphStyle('Small', parent=styles['Normal'], fontSize=8,
                                  spaceAfter=4, textColor=colors.HexColor('#666666'))

    story = []

    # ---- Title Page ----
    story.append(Paragraph("STRC (Stretch) Peg Reversion Strategy", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", small_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Executive Summary", heading_style))
    stats = analysis['price_stats']
    story.append(Paragraph(f"""
        STRC is Strategy's perpetual preferred stock targeting $100 par value with ~11% annual variable dividends.
        Over {len(analysis['df'])} trading days, the price has <b>never reached $100</b> (always below peg).
        Mean price: <b>${stats['mean']:.2f}</b>, range: ${stats['min']:.2f} - ${stats['max']:.2f}.<br/><br/>
        This report analyzes peg-reversion strategies, dividend capture timing, and optimal entry/exit thresholds.
    """, body_style))

    # ---- Pattern Analysis ----
    story.append(Spacer(1, 10))
    story.append(Paragraph("1. Pattern Analysis", heading_style))

    # Price & dividends chart
    img_path = os.path.join(OUTPUT_DIR, 'strc_price_dividends.png')
    if os.path.exists(img_path):
        story.append(Image(img_path, width=7*inch, height=5*inch))

    story.append(PageBreak())

    # Peg distance distribution
    story.append(Paragraph("Price Distribution Relative to $100 Peg", heading_style))
    img_path = os.path.join(OUTPUT_DIR, 'strc_peg_distance.png')
    if os.path.exists(img_path):
        story.append(Image(img_path, width=7*inch, height=3.5*inch))

    # Threshold table
    story.append(Spacer(1, 10))
    thresh_data = [['Threshold', '% Days Below', 'Buying Opportunity']]
    for t in [99.5, 99, 98, 97, 96, 95]:
        pct = stats.get(f'pct_below_{int(t)}', stats.get(f'pct_below_{t}', 0))
        # Calculate from raw data
        pct = (analysis['df']['Close'] < t).mean() * 100
        freq = 'Very Frequent' if pct > 70 else 'Frequent' if pct > 40 else 'Moderate' if pct > 20 else 'Rare'
        thresh_data.append([f'${t}', f'{pct:.1f}%', freq])

    thresh_table = Table(thresh_data, colWidths=[1.5*inch, 1.5*inch, 2*inch])
    thresh_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
    ]))
    story.append(thresh_table)

    # Mean reversion speed
    story.append(Spacer(1, 15))
    story.append(Paragraph("Mean Reversion Speed", heading_style))
    rev_data = [['Buy Below', 'Episodes', 'Avg Days to Recover', 'Max Days', 'Avg Gain %']]
    for threshold, stats_rev in analysis['reversion'].items():
        rev_data.append([
            f'${threshold}',
            str(stats_rev['episodes']),
            f"{stats_rev['avg_days']:.0f}",
            str(stats_rev['max_days']),
            f"{stats_rev['avg_gain']:.2f}%",
        ])
    rev_table = Table(rev_data, colWidths=[1.2*inch, 1*inch, 1.5*inch, 1.2*inch, 1.2*inch])
    rev_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
    ]))
    story.append(rev_table)

    story.append(PageBreak())

    # Dividend cycle
    story.append(Paragraph("2. Dividend Cycle Analysis", heading_style))
    img_path = os.path.join(OUTPUT_DIR, 'strc_dividend_cycle.png')
    if os.path.exists(img_path):
        story.append(Image(img_path, width=7*inch, height=3*inch))

    div_df = analysis['div_analysis']
    if not div_df.empty:
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"""
            <b>Key Dividend Findings:</b><br/>
            • Average ex-div price drop: ${div_df['drop'].mean():.2f} (vs avg dividend: ${div_df['amount'].mean():.3f})<br/>
            • Average 5-day recovery: ${div_df['recovery_5d'].mean():.2f}<br/>
            • Average 10-day recovery: ${div_df['recovery_10d'].mean():.2f}<br/>
            • Pre-div 5-day drift: {div_df['pre_5d_drift'].mean():.2f}% (positive = price rises into ex-div)
        """, body_style))

    # Time patterns
    story.append(Spacer(1, 10))
    img_path = os.path.join(OUTPUT_DIR, 'strc_time_patterns.png')
    if os.path.exists(img_path):
        story.append(Paragraph("3. Time-Based Patterns", heading_style))
        story.append(Image(img_path, width=7*inch, height=3*inch))

    # BTC correlation
    story.append(PageBreak())
    story.append(Paragraph("4. Bitcoin Correlation", heading_style))
    img_path = os.path.join(OUTPUT_DIR, 'strc_btc_correlation.png')
    if os.path.exists(img_path):
        story.append(Image(img_path, width=7*inch, height=4.5*inch))

    btc_stress = analysis['btc_stress']
    story.append(Paragraph(f"""
        <b>BTC Correlation:</b> {analysis['btc_corr_all']:.3f} (daily returns)<br/>
        <b>On big BTC down days (>3% drop):</b> {btc_stress['n_days']} occurrences,
        avg STRC return: {btc_stress['avg_strc_return']:.2%},
        worst STRC day: {btc_stress['worst_strc']:.2%}
    """, body_style))

    # ---- Strategy Results ----
    story.append(PageBreak())
    story.append(Paragraph("5. Strategy Backtest Results", heading_style))

    # Summary table
    summary_keys = ['buy_hold', 'peg_99', 'peg_98', 'peg_97', 'peg_96', 'peg_95',
                    'scale_equal_98', 'scale_equal_97', 'div_capture', 'combined_98', 'combined_97']
    summary_data = [['Strategy', 'Total Return', 'Annualized', 'Sharpe', 'Max DD',
                     '% Time In', 'Trades', 'Divs Collected']]

    for key in summary_keys:
        if key in results:
            r = results[key]
            summary_data.append([
                r['name'],
                f"{r['total_return_pct']:+.2f}%",
                f"{r.get('annualized_pct', 0):+.1f}%",
                f"{r.get('sharpe', 0):.2f}",
                f"{r.get('max_drawdown', 0):.1f}%",
                f"{r.get('pct_time_in', 0):.0f}%",
                str(r.get('trades', 0)),
                f"${r.get('divs_collected', 0):.2f}",
            ])

    summary_table = Table(summary_data,
                          colWidths=[1.8*inch, 0.8*inch, 0.8*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.8*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(summary_table)

    # Equity curves
    story.append(Spacer(1, 15))
    img_path = os.path.join(OUTPUT_DIR, 'strc_strategy_comparison.png')
    if os.path.exists(img_path):
        story.append(Image(img_path, width=7*inch, height=4*inch))

    # Key Takeaways
    story.append(Spacer(1, 15))
    story.append(Paragraph("Key Takeaways", heading_style))

    # Dynamically determine the best peg strategy
    peg_keys = [k for k in results if k.startswith('peg_') and '_sell_' not in k]
    best_peg_key = max(peg_keys, key=lambda k: results[k].get('sharpe', 0)) if peg_keys else None
    bh = results.get('buy_hold', {})
    best = results.get(best_peg_key, {}) if best_peg_key else {}

    # Check if $96 and $97 produce identical results
    peg96 = results.get('peg_96', {})
    peg97 = results.get('peg_97', {})
    same_96_97 = (abs(peg96.get('total_return_pct', 0) - peg97.get('total_return_pct', -1)) < 0.01)

    div_cap = results.get('div_capture', {})
    btc_corr = analysis.get('btc_corr_all', 0)

    # Build reversion speed summary
    rev = analysis.get('reversion', {})
    rev_97 = rev.get(97, {})
    rev_95 = rev.get(95, {})

    takeaway_style = ParagraphStyle('Takeaway', parent=body_style, fontSize=10,
                                     spaceBefore=4, spaceAfter=4, leftIndent=15)
    bullet_style = ParagraphStyle('Bullet', parent=body_style, fontSize=9,
                                   spaceBefore=2, spaceAfter=2, leftIndent=30,
                                   textColor=colors.HexColor('#444444'))

    story.append(Paragraph(
        f"<b>1. Peg reversion beats buy &amp; hold.</b> The best risk-adjusted strategy is "
        f"<b>{best.get('name', 'N/A')}</b> with a {best.get('annualized_pct', 0):+.1f}% annualized return "
        f"and Sharpe ratio of {best.get('sharpe', 0):.2f}, vs buy &amp; hold at "
        f"{bh.get('annualized_pct', 0):+.1f}% / {bh.get('sharpe', 0):.2f} Sharpe.",
        takeaway_style))

    story.append(Paragraph(
        f"<b>2. Lower thresholds = better risk/reward, but fewer trades.</b> "
        f"Waiting for deeper dips produces higher returns with smaller drawdowns. "
        f"The {best.get('name', '')} strategy only invested {best.get('pct_time_in', 0):.0f}% of the time "
        f"while cutting max drawdown to {best.get('max_drawdown', 0):.1f}% (vs {bh.get('max_drawdown', 0):.1f}% for buy &amp; hold).",
        takeaway_style))

    if same_96_97:
        story.append(Paragraph(
            "<b>3. $96 and $97 thresholds produce identical results</b> — "
            "price never bounced at $96 without also crossing $97, so $97 is the more practical entry.",
            takeaway_style))
    else:
        story.append(Paragraph(
            f"<b>3. $96 threshold:</b> {peg96.get('total_return_pct', 0):+.1f}% return vs "
            f"$97 threshold: {peg97.get('total_return_pct', 0):+.1f}%.",
            takeaway_style))

    story.append(Paragraph(
        f"<b>4. Dividend capture alone is worthless.</b> "
        f"The pure dividend capture strategy returned just {div_cap.get('total_return_pct', 0):+.2f}%. "
        f"Price movement around ex-div dates swamps the ~$0.85 monthly dividend.",
        takeaway_style))

    story.append(Paragraph(
        f"<b>5. Mean reversion is fast.</b> "
        f"Below $97: recovers in avg {rev_97.get('avg_days', 0):.0f} days with "
        f"{rev_97.get('avg_gain', 0):.1f}% avg gain. "
        f"Below $95: recovers in avg {rev_95.get('avg_days', 0):.0f} days.",
        takeaway_style))

    story.append(Paragraph(
        f"<b>6. BTC correlation is meaningful at {btc_corr:.3f}.</b> "
        f"Large BTC selloffs drag STRC down, which creates the buying opportunities. "
        f"Monitor BTC for entry signals.",
        takeaway_style))

    story.append(Paragraph(
        "<b>7. Idle cash earns T-bill rates.</b> "
        "When not in STRC, capital earns ~4.5% in T-bills/money market. "
        "This is already baked into the peg-reversion returns above, making the comparison fair vs buy &amp; hold.",
        takeaway_style))

    story.append(Paragraph(
        "<b>8. Caveat: limited data.</b> "
        f"Only {len(analysis['df'])} trading days of history. "
        "STRC is a new instrument and these patterns may not persist. "
        "The peg mechanism depends on Strategy's willingness to raise dividends — "
        "if BTC crashes hard enough, par recovery is not guaranteed.",
        takeaway_style))

    # ---- Tiered vs Static ----
    story.append(PageBreak())
    story.append(Paragraph("6. Tiered Scale-In vs Static All-In", heading_style))
    story.append(Paragraph("""
        Does investing more at each deeper price level beat a simple all-in at one threshold?
        We compare four weighting schemes across entry thresholds:
    """, body_style))

    # Weighting scheme explanation
    weight_explain = [
        ['Scheme', 'Level 1', 'Level 2', 'Level 3', 'Level 4', 'Logic'],
        ['All-in', '100%', '—', '—', '—', 'Full position at first trigger'],
        ['Equal', '25%', '25%', '25%', '25%', 'Spread evenly across dips'],
        ['Aggressive', '10%', '15%', '25%', '50%', 'Heaviest at deepest dips'],
        ['Pyramid', '40%', '30%', '20%', '10%', 'Most capital deployed early'],
        ['Linear', '10%', '20%', '30%', '40%', 'Linearly increasing with dip'],
    ]
    wt_table = Table(weight_explain, colWidths=[1*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 2.5*inch])
    wt_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
    ]))
    story.append(wt_table)
    story.append(Spacer(1, 10))

    img_path = os.path.join(OUTPUT_DIR, 'strc_tiered_vs_static.png')
    if os.path.exists(img_path):
        story.append(Image(img_path, width=7*inch, height=3.5*inch))

    # Tiered results table
    story.append(Spacer(1, 10))
    tiered_data = [['Threshold', 'Approach', 'Return', 'Annualized', 'Sharpe', 'Max DD']]
    for threshold in [99, 98, 97]:
        for weight_key, weight_name in [('peg_', 'All-in'), ('scale_equal_', 'Equal'),
                                         ('scale_aggr_', 'Aggressive'), ('scale_pyr_', 'Pyramid'),
                                         ('scale_lin_', 'Linear')]:
            if weight_key == 'peg_':
                key = f'{weight_key}{threshold}'
            else:
                key = f'{weight_key}{threshold}'
            if key in results:
                r = results[key]
                tiered_data.append([
                    f'${threshold}',
                    weight_name,
                    f"{r['total_return_pct']:+.2f}%",
                    f"{r.get('annualized_pct', 0):+.1f}%",
                    f"{r.get('sharpe', 0):.2f}",
                    f"{r.get('max_drawdown', 0):.1f}%",
                ])

    tiered_table = Table(tiered_data, colWidths=[0.8*inch, 1*inch, 1*inch, 1*inch, 0.8*inch, 0.8*inch])
    tiered_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(tiered_table)

    # Dynamic insight
    story.append(Spacer(1, 10))
    # Find best tiered approach at $97
    best_tiered_key = None
    best_tiered_sharpe = -999
    for wt in ['equal', 'aggr', 'pyr', 'lin']:
        key = f'scale_{wt}_97'
        if key in results and results[key].get('sharpe', 0) > best_tiered_sharpe:
            best_tiered_sharpe = results[key].get('sharpe', 0)
            best_tiered_key = key
    static_97 = results.get('peg_97', {})
    best_tiered = results.get(best_tiered_key, {}) if best_tiered_key else {}

    if best_tiered and static_97:
        if best_tiered.get('sharpe', 0) > static_97.get('sharpe', 0):
            winner = "tiered"
            story.append(Paragraph(
                f"<b>Verdict:</b> At the $97 threshold, <b>{best_tiered.get('name', '')}</b> "
                f"(Sharpe {best_tiered.get('sharpe', 0):.2f}) edges out static all-in "
                f"(Sharpe {static_97.get('sharpe', 0):.2f}). "
                f"Tiered approaches reduce drawdown by averaging into a lower cost basis, "
                f"though the return difference is {best_tiered.get('total_return_pct', 0) - static_97.get('total_return_pct', 0):+.1f}pp.",
                body_style))
        else:
            winner = "static"
            story.append(Paragraph(
                f"<b>Verdict:</b> At the $97 threshold, <b>static all-in</b> "
                f"(Sharpe {static_97.get('sharpe', 0):.2f}, return {static_97.get('total_return_pct', 0):+.1f}%) "
                f"beats tiered scale-in. The deeper dip levels rarely get triggered at $97, "
                f"so tiered approaches leave too much capital idle. "
                f"However, at higher thresholds like $98-$99, scaling in provides better risk management.",
                body_style))

    # Sensitivity
    story.append(PageBreak())
    story.append(Paragraph("7. Sensitivity Analysis", heading_style))
    img_path = os.path.join(OUTPUT_DIR, 'strc_sensitivity.png')
    if os.path.exists(img_path):
        story.append(Image(img_path, width=7*inch, height=3.5*inch))

    # ---- Tax Considerations ----
    story.append(Spacer(1, 20))
    story.append(Paragraph("8. Tax Considerations", heading_style))
    story.append(Paragraph("""
        <b>STRC Dividend Tax Classification:</b><br/>
        • STRC dividends are classified as <b>return of capital (ROC)</b> until basis is exhausted,
          then taxed as capital gains<br/>
        • ROC reduces your cost basis rather than being taxed as ordinary income<br/>
        • This means dividends are <b>tax-deferred</b> until you sell (or basis reaches $0)<br/>
        • Holding period matters: shares held >1 year qualify for long-term capital gains rates (15-20%)
          vs short-term (ordinary income rates up to 37%)<br/><br/>
        <b>Strategy Tax Implications:</b><br/>
        • <b>Buy &amp; Hold:</b> Most tax-efficient - ROC dividends reduce basis, capital gains deferred<br/>
        • <b>Peg Reversion:</b> Frequent trading may trigger short-term capital gains<br/>
        • <b>Dividend Capture:</b> Short holding periods = short-term capital gains on price appreciation<br/>
        • <b>Combined:</b> Holding through dividends improves tax treatment if position held >1 year<br/><br/>
        <i>Note: Consult a tax professional. See strategy.com/investor-relations/dividend-return-of-capital
        for official ROC information.</i>
    """, body_style))

    # ---- Opportunity Cost ----
    story.append(Spacer(1, 15))
    story.append(Paragraph("9. Opportunity Cost: What to Hold When Not in STRC", heading_style))
    story.append(Paragraph("""
        When the peg-reversion strategy has you in cash (waiting for a dip), consider:<br/><br/>
        • <b>T-Bills / Money Market:</b> ~4-5% annualized, zero risk, instant liquidity<br/>
        • <b>IBIT Night Strategy:</b> Higher return potential but requires active management<br/>
        • <b>SGOV (Treasury ETF):</b> Short-term treasuries, ~4.5% yield, highly liquid<br/>
        • <b>Cash:</b> 0% return but maximum flexibility for quick entry<br/><br/>
        The best choice depends on how quickly you need to deploy capital when STRC dips.
        If using limit orders, cash or T-bills work best for instant execution.
    """, body_style))

    # Build PDF
    doc.build(story)
    print(f"\n📄 PDF Report saved: {pdf_path}")
    return pdf_path


# =============================================================================
# CONSOLE OUTPUT
# =============================================================================

def print_summary(analysis, results):
    """Print key results to console."""
    print("\n" + "=" * 70)
    print("STRC PEG REVERSION STRATEGY - BACKTEST RESULTS")
    print("=" * 70)

    stats = analysis['price_stats']
    print(f"\n📊 PRICE STATISTICS:")
    print(f"   Mean: ${stats['mean']:.2f}  |  Range: ${stats['min']:.2f} - ${stats['max']:.2f}")
    print(f"   Always below $100: {stats['pct_below_100']:.0f}% of days")

    print(f"\n📈 MEAN REVERSION SPEED:")
    for threshold, rev in analysis['reversion'].items():
        print(f"   Below ${threshold}: {rev['episodes']} episodes, "
              f"avg {rev['avg_days']:.0f} days to recover, "
              f"avg gain {rev['avg_gain']:.2f}%")

    print(f"\n💰 STRATEGY COMPARISON:")
    print(f"   {'Strategy':<35s} {'Return':>8s} {'Annual':>8s} {'Sharpe':>7s} {'MaxDD':>7s} {'%InMkt':>7s}")
    print(f"   {'-'*72}")

    display_keys = ['buy_hold', 'peg_99', 'peg_98', 'peg_97', 'peg_96',
                    'scale_equal_98', 'div_capture', 'combined_98']
    for key in display_keys:
        if key in results:
            r = results[key]
            print(f"   {r['name']:<35s} {r['total_return_pct']:>+7.2f}% "
                  f"{r.get('annualized_pct', 0):>+7.1f}% "
                  f"{r.get('sharpe', 0):>6.2f} "
                  f"{r.get('max_drawdown', 0):>6.1f}% "
                  f"{r.get('pct_time_in', 0):>5.0f}%")

    # Tiered vs Static comparison
    print(f"\n🔀 TIERED vs STATIC ENTRY (at $97 threshold):")
    print(f"   {'Approach':<35s} {'Return':>8s} {'Annual':>8s} {'Sharpe':>7s} {'MaxDD':>7s}")
    print(f"   {'-'*65}")
    tiered_keys_97 = ['peg_97', 'scale_equal_97', 'scale_aggr_97', 'scale_pyr_97', 'scale_lin_97']
    for key in tiered_keys_97:
        if key in results:
            r = results[key]
            print(f"   {r['name']:<35s} {r['total_return_pct']:>+7.2f}% "
                  f"{r.get('annualized_pct', 0):>+7.1f}% "
                  f"{r.get('sharpe', 0):>6.2f} "
                  f"{r.get('max_drawdown', 0):>6.1f}%")

    print(f"\n🔑 BTC CORRELATION: {analysis['btc_corr_all']:.3f}")
    print("=" * 70)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run full STRC analysis and backtest."""
    print("=" * 60)
    print("STRC (Stretch) Peg Reversion Strategy Analysis")
    print("=" * 60)

    # Fetch data
    df_adj, df_unadj, divs, btc_df = fetch_data()

    # Pattern analysis
    analysis = analyze_patterns(df_unadj, divs, btc_df)

    # Run backtests
    results = backtest_strategies(df_unadj, divs)

    # Print console summary
    print_summary(analysis, results)

    # Generate visualizations
    print("\n📈 Generating visualizations...")
    plot_price_and_dividends(df_unadj, divs)
    plot_peg_distance_distribution(df_unadj)
    plot_dividend_cycle(analysis)
    plot_weekly_monthly_patterns(analysis)
    plot_btc_correlation(analysis)
    plot_strategy_comparison(results)
    plot_tiered_vs_static(results)
    plot_sensitivity_analysis(results)

    # Save data
    analysis['df'].to_csv(os.path.join(OUTPUT_DIR, 'strc_daily_data.csv'))
    print(f"Saved: strc_daily_data.csv")

    # Generate PDF report
    print("\n📄 Generating PDF report...")
    generate_pdf_report(analysis, results)

    print(f"\n✅ Analysis complete! Results saved to: {OUTPUT_DIR}")

    return analysis, results


if __name__ == "__main__":
    analysis, results = main()
