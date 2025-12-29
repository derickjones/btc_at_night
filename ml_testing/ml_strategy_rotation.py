"""
IBIT+SPY Rotation Strategy - ML Model
=====================================
Uses features available at 3:50 PM to predict two separate decisions:
- Decision 1: Whether to buy IBIT overnight (probability of positive overnight return)
- Decision 2: Whether to buy SPY during the day (probability of positive day retu            # Train model
            if name == 'Logistic Regression':
                model.fit(X_train_scaled, y_train)
                y_pred_train = model.predict(X_train_scaled)
                y_pred_test = model.predict(X_test_scaled)
                y_prob_test = model.predict_proba(X_test_scaled)[:, 1]
            else:
                model.fit(X_train, y_train)  # Tree models use unscaled features
                y_pred_train = model.predict(X_train)
                y_pred_test = model.predict(X_test)
                y_prob_test = model.predict_proba(X_test)[:, 1] decisions use intraday data available at 3:50 PM including gap, intraday return, range, volume, etc.
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

from sklearn.model_selection import train_test_split, TimeSeriesSplit, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except (ImportError, Exception):
    HAS_XGBOOST = False

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output_rotation_ml')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def fetch_data():
    """Fetch IBIT and SPY historical data with minute-level data for 3:50 PM prices."""
    print("📊 Fetching IBIT and SPY data...")

    start_date = "2024-01-11"
    end_date = datetime.now().strftime("%Y-%m-%d")

    ibit = yf.Ticker("IBIT")
    spy = yf.Ticker("SPY")

    # Get daily data for returns calculation
    ibit_df = ibit.history(start=start_date, end=end_date)
    spy_df = spy.history(start=start_date, end=end_date)

    print(f"   IBIT: {len(ibit_df)} trading days")
    print(f"   SPY: {len(spy_df)} trading days")

    # Get minute-level data to extract 3:50 PM prices
    print("📊 Fetching minute-level data for 3:50 PM prices...")

    # For each trading day, get minute data and extract 3:50 PM price
    ibit_3_50_prices = {}
    spy_3_50_prices = {}

    for date in ibit_df.index:
        date_str = date.strftime("%Y-%m-%d")

        try:
            # Get minute data for this specific day
            day_start = date.strftime("%Y-%m-%d")
            day_end = (date + timedelta(days=1)).strftime("%Y-%m-%d")

            ibit_minute = ibit.history(start=day_start, end=day_end, interval="1m")
            spy_minute = spy.history(start=day_start, end=day_end, interval="1m")

            # Find 3:50 PM price (15:50:00)
            # Market closes at 16:00, so 3:50 PM is 15:50
            target_time = pd.Timestamp(f"{date_str} 15:50:00")

            # Get the price closest to 3:50 PM (within the last hour of trading)
            ibit_afternoon = ibit_minute[ibit_minute.index.time >= pd.Timestamp("14:00:00").time()]
            spy_afternoon = spy_minute[spy_minute.index.time >= pd.Timestamp("14:00:00").time()]

            if not ibit_afternoon.empty:
                # Get the last price before/at 3:50 PM
                ibit_3_50_prices[date] = ibit_afternoon['Close'].iloc[-1]  # Last price in afternoon
            else:
                # Fallback to close if no afternoon data
                ibit_3_50_prices[date] = ibit_df.loc[date, 'Close']

            if not spy_afternoon.empty:
                spy_3_50_prices[date] = spy_afternoon['Close'].iloc[-1]  # Last price in afternoon
            else:
                # Fallback to close if no afternoon data
                spy_3_50_prices[date] = spy_df.loc[date, 'Close']

        except Exception as e:
            print(f"   Warning: Could not get minute data for {date_str}: {e}")
            # Fallback to close price
            ibit_3_50_prices[date] = ibit_df.loc[date, 'Close']
            spy_3_50_prices[date] = spy_df.loc[date, 'Close']

    # Add 3:50 PM prices to the dataframes
    ibit_df['ibit_3_50_price'] = pd.Series(ibit_3_50_prices)
    spy_df['spy_3_50_price'] = pd.Series(spy_3_50_prices)

    print(f"   Extracted 3:50 PM prices for {len(ibit_3_50_prices)} days")

    return ibit_df, spy_df


def create_features(ibit_df, spy_df):
    """
    Create feature matrix for dual ML decisions in rotation strategy.

    Features available at 3:50 PM for predicting:
    - Decision 1: IBIT overnight return direction (positive/negative)
    - Decision 2: SPY day return direction (positive/negative)
    """
    print("🔧 Engineering ROTATION features (available at 3:50 PM)...")

    df = ibit_df.copy()
    df = df.rename(columns={
        'Open': 'ibit_open',
        'High': 'ibit_high',
        'Low': 'ibit_low',
        'Close': 'ibit_close',
        'Volume': 'ibit_volume'
    })

    # Add SPY data
    spy_aligned = spy_df.reindex(df.index)
    df['spy_open'] = spy_aligned['Open']
    df['spy_high'] = spy_aligned['High']
    df['spy_low'] = spy_aligned['Low']
    df['spy_close'] = spy_aligned['Close']
    df['spy_volume'] = spy_aligned['Volume']
    df['spy_3_50_price'] = spy_aligned['spy_3_50_price']

    # Calculate strategy returns
    df['ibit_overnight_return'] = (df['ibit_open'].shift(-1) - df['ibit_close']) / df['ibit_close']
    df['spy_day_return'] = (df['spy_close'] - df['spy_open']) / df['spy_open']
    df['rotation_return'] = df['ibit_overnight_return'] + df['spy_day_return']
    df['ibit_hold_return'] = df['ibit_close'].pct_change()

    # ============ DATETIME FEATURES (Always available) ============
    df['day_of_week'] = df.index.dayofweek
    df['month'] = df.index.month
    df['day_of_month'] = df.index.day
    df['week_of_year'] = df.index.isocalendar().week.astype(int)
    df['quarter'] = df.index.quarter

    df['is_monday'] = (df['day_of_week'] == 0).astype(int)
    df['is_friday'] = (df['day_of_week'] == 4).astype(int)
    df['is_month_start'] = (df['day_of_month'] <= 5).astype(int)
    df['is_month_end'] = (df['day_of_month'] >= 25).astype(int)

    # ============ SAME-DAY INTRADAY FEATURES (Available at 3:50 PM) ============

    # IBIT Gap: How did IBIT open relative to yesterday's close?
    df['ibit_today_gap'] = (df['ibit_open'] - df['ibit_close'].shift(1)) / df['ibit_close'].shift(1)
    df['spy_today_gap'] = (df['spy_open'] - df['spy_close'].shift(1)) / df['spy_close'].shift(1)
    df['gap_vs_spy'] = df['ibit_today_gap'] - df['spy_today_gap']

    # Intraday returns: How have both assets performed today? (using 3:50 PM price, not close)
    df['ibit_intraday_return'] = (df['ibit_3_50_price'] - df['ibit_open']) / df['ibit_open']
    df['spy_intraday_return'] = (df['spy_3_50_price'] - df['spy_open']) / df['spy_open']
    df['intraday_vs_spy'] = df['ibit_intraday_return'] - df['spy_intraday_return']

    # Intraday ranges: Today's volatility for both assets
    df['ibit_intraday_range'] = (df['ibit_high'] - df['ibit_low']) / df['ibit_open']
    df['spy_intraday_range'] = (df['spy_high'] - df['spy_low']) / df['spy_open']
    df['range_vs_spy'] = df['ibit_intraday_range'] - df['spy_intraday_range']

    # Where in today's range are current prices? (using 3:50 PM price, not close)
    df['ibit_intraday_position'] = (df['ibit_3_50_price'] - df['ibit_low']) / (df['ibit_high'] - df['ibit_low'])
    df['spy_intraday_position'] = (df['spy_3_50_price'] - df['spy_low']) / (df['spy_high'] - df['spy_low'])
    df['ibit_intraday_position'] = df['ibit_intraday_position'].fillna(0.5)
    df['spy_intraday_position'] = df['spy_intraday_position'].fillna(0.5)

    # Today's volume (scaled to approximate 3:50 PM)
    df['ibit_today_volume_scaled'] = df['ibit_volume'] * 0.9
    df['spy_today_volume_scaled'] = df['spy_volume'] * 0.9
    df['ibit_spy_vol_ratio'] = df['ibit_today_volume_scaled'] / df['spy_today_volume_scaled']

    # Volume vs recent averages
    df['ibit_volume_vs_ma5'] = df['ibit_today_volume_scaled'] / df['ibit_volume'].shift(1).rolling(5).mean()
    df['spy_volume_vs_ma5'] = df['spy_today_volume_scaled'] / df['spy_volume'].shift(1).rolling(5).mean()

    # ============ PREVIOUS ROTATION RETURNS ============
    df['prev_rotation_1'] = df['rotation_return'].shift(1)
    df['prev_rotation_2'] = df['rotation_return'].shift(2)
    df['prev_rotation_3'] = df['rotation_return'].shift(3)
    df['prev_rotation_5_avg'] = df['rotation_return'].shift(1).rolling(5).mean()
    df['prev_rotation_5_std'] = df['rotation_return'].shift(1).rolling(5).std()
    df['prev_rotation_10_avg'] = df['rotation_return'].shift(1).rolling(10).mean()

    # ============ PREVIOUS COMPONENT RETURNS ============
    df['prev_ibit_overnight_1'] = df['ibit_overnight_return'].shift(1)
    df['prev_ibit_overnight_2'] = df['ibit_overnight_return'].shift(2)
    df['prev_spy_day_1'] = df['spy_day_return'].shift(1)
    df['prev_spy_day_2'] = df['spy_day_return'].shift(2)

    # ============ PRIOR DAY RETURNS ============
    df['ibit_prior_day_return'] = df['ibit_close'].shift(1).pct_change(1)
    df['ibit_prior_5d_return'] = df['ibit_close'].shift(1).pct_change(5)
    df['ibit_prior_10d_return'] = df['ibit_close'].shift(1).pct_change(10)
    df['ibit_prior_20d_return'] = df['ibit_close'].shift(1).pct_change(20)

    df['spy_prior_day_return'] = df['spy_close'].shift(1).pct_change(1)
    df['spy_prior_5d_return'] = df['spy_close'].shift(1).pct_change(5)
    df['spy_prior_10d_return'] = df['spy_close'].shift(1).pct_change(10)

    df['ibit_vs_spy_prior_1d'] = df['ibit_prior_day_return'] - df['spy_prior_day_return']
    df['ibit_vs_spy_prior_5d'] = df['ibit_prior_5d_return'] - df['spy_prior_5d_return']
    df['ibit_vs_spy_prior_10d'] = df['ibit_prior_10d_return'] - df['spy_prior_10d_return']

    # ============ PRIOR VOLATILITY ============
    ibit_prior_returns = df['ibit_close'].shift(1).pct_change()
    spy_prior_returns = df['spy_close'].shift(1).pct_change()

    df['ibit_prior_volatility_5d'] = ibit_prior_returns.rolling(5).std()
    df['ibit_prior_volatility_10d'] = ibit_prior_returns.rolling(10).std()
    df['spy_prior_volatility_5d'] = spy_prior_returns.rolling(5).std()
    df['spy_prior_volatility_10d'] = spy_prior_returns.rolling(10).std()

    # ============ PRICE LEVEL FEATURES ============
    df['ibit_prior_close'] = df['ibit_close'].shift(1)
    df['ibit_prior_close_ma5'] = df['ibit_close'].shift(1).rolling(5).mean()
    df['ibit_prior_close_ma20'] = df['ibit_close'].shift(1).rolling(20).mean()
    df['ibit_prior_close_vs_ma5'] = df['ibit_prior_close'] / df['ibit_prior_close_ma5'] - 1
    df['ibit_prior_close_vs_ma20'] = df['ibit_prior_close'] / df['ibit_prior_close_ma20'] - 1

    df['spy_prior_close'] = df['spy_close'].shift(1)
    df['spy_prior_close_ma5'] = df['spy_close'].shift(1).rolling(5).mean()
    df['spy_prior_close_ma20'] = df['spy_close'].shift(1).rolling(20).mean()

    # Current price vs MAs (available at 3:50 PM)
    df['ibit_current_vs_ma5'] = df['ibit_close'] / df['ibit_prior_close_ma5'] - 1
    df['ibit_current_vs_ma20'] = df['ibit_close'] / df['ibit_prior_close_ma20'] - 1
    df['spy_current_vs_ma5'] = df['spy_close'] / df['spy_prior_close_ma5'] - 1
    df['spy_current_vs_ma20'] = df['spy_close'] / df['spy_prior_close_ma20'] - 1

    # ============ CORRELATION FEATURES ============
    # Rolling correlation between IBIT and SPY
    df['ibit_spy_corr_5d'] = ibit_prior_returns.rolling(5).corr(spy_prior_returns)
    df['ibit_spy_corr_10d'] = ibit_prior_returns.rolling(10).corr(spy_prior_returns)

    # ============ TARGET VARIABLES ============
    # Decision 1: IBIT overnight return direction (1 = positive, 0 = negative)
    df['target_ibit_overnight'] = (df['ibit_overnight_return'] > 0).astype(int)

    # Decision 2: SPY day return direction (1 = positive, 0 = negative)
    df['target_spy_day'] = (df['spy_day_return'] > 0).astype(int)

    # Drop NaN rows
    df = df.dropna()

    print(f"   Created rotation + intraday features")
    print(f"   IBIT overnight positive rate: {df['target_ibit_overnight'].mean():.1%}")
    print(f"   SPY day positive rate: {df['target_spy_day'].mean():.1%}")
    print(f"   {len(df)} samples after dropping NaN")

    return df


def get_feature_columns():
    """Return list of features available at 3:50 PM for rotation prediction."""
    return [
        # Datetime features
        'day_of_week', 'month', 'day_of_month', 'week_of_year', 'quarter',
        'is_monday', 'is_friday', 'is_month_start', 'is_month_end',

        # SAME-DAY INTRADAY features
        'ibit_today_gap', 'spy_today_gap', 'gap_vs_spy',
        'ibit_intraday_return', 'spy_intraday_return', 'intraday_vs_spy',
        'ibit_intraday_range', 'spy_intraday_range', 'range_vs_spy',
        'ibit_intraday_position', 'spy_intraday_position',
        'ibit_spy_vol_ratio', 'ibit_volume_vs_ma5', 'spy_volume_vs_ma5',
        'ibit_current_vs_ma5', 'ibit_current_vs_ma20',
        'spy_current_vs_ma5', 'spy_current_vs_ma20',

        # Previous rotation returns
        'prev_rotation_1', 'prev_rotation_2', 'prev_rotation_3',
        'prev_rotation_5_avg', 'prev_rotation_5_std', 'prev_rotation_10_avg',

        # Previous component returns
        'prev_ibit_overnight_1', 'prev_ibit_overnight_2',
        'prev_spy_day_1', 'prev_spy_day_2',

        # Prior day returns
        'ibit_prior_day_return', 'ibit_prior_5d_return', 'ibit_prior_10d_return', 'ibit_prior_20d_return',
        'spy_prior_day_return', 'spy_prior_5d_return', 'spy_prior_10d_return',
        'ibit_vs_spy_prior_1d', 'ibit_vs_spy_prior_5d', 'ibit_vs_spy_prior_10d',

        # Prior volatility
        'ibit_prior_volatility_5d', 'ibit_prior_volatility_10d',
        'spy_prior_volatility_5d', 'spy_prior_volatility_10d',

        # Price level features
        'ibit_prior_close_vs_ma5', 'ibit_prior_close_vs_ma20',

        # Correlation features
        'ibit_spy_corr_5d', 'ibit_spy_corr_10d'
    ]


def train_models(df):
    """Train separate ML models for IBIT overnight and SPY day decisions."""
    print("\n🤖 Training ML models (dual rotation decisions)...")

    feature_cols = get_feature_columns()

    # Time-series split
    split_idx = int(len(df) * 0.7)

    X = df[feature_cols]
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]

    print(f"   Training samples: {len(X_train)}")
    print(f"   Test samples: {len(X_test)}")

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    models = {
        'Random Forest': RandomForestClassifier(
            n_estimators=100, max_depth=5, min_samples_leaf=10, random_state=42
        ),
        'Gradient Boosting': GradientBoostingClassifier(
            n_estimators=100, max_depth=3, min_samples_leaf=10, random_state=42
        ),
        'Logistic Regression': LogisticRegression(
            random_state=42, max_iter=1000
        )
    }

    if HAS_XGBOOST:
        models['XGBoost'] = XGBClassifier(
            n_estimators=100, max_depth=3, min_child_weight=10, random_state=42,
            use_label_encoder=False, eval_metric='logloss', verbosity=0
        )

    results = {}

    # Train models for both decisions
    for decision_name, target_col in [('IBIT_Overnight', 'target_ibit_overnight'), ('SPY_Day', 'target_spy_day')]:
        print(f"\n   Training models for {decision_name} decision...")
        y = df[target_col]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        print(f"     Positive class ratio: {y_train.mean():.1%}")

        results[decision_name] = {}

        for name, model in models.items():
            print(f"     Training {name}...")

            # Train model
            model.fit(X_train_scaled, y_train)

            # Predictions
            y_pred_train = model.predict(X_train_scaled)
            y_pred_test = model.predict(X_test_scaled)

            # Calculate probabilities
            y_prob_test = model.predict_proba(X_test_scaled)[:, 1]

            # Metrics
            results[decision_name][name] = {
                'model': model,
                'scaler': scaler,
                'train_accuracy': accuracy_score(y_train, y_pred_train),
                'test_accuracy': accuracy_score(y_test, y_pred_test),
                'train_precision': precision_score(y_train, y_pred_train),
                'test_precision': precision_score(y_test, y_pred_test),
                'train_recall': recall_score(y_train, y_pred_train),
                'test_recall': recall_score(y_test, y_pred_test),
                'train_f1': f1_score(y_train, y_pred_train),
                'test_f1': f1_score(y_test, y_pred_test),
                'feature_importance': None,
                'X_test': X_test,
                'y_test': y_test,
                'y_pred_test': y_pred_test,
                'y_prob_test': y_prob_test
            }

            # Feature importance for tree-based models
            if hasattr(model, 'feature_importances_'):
                results[decision_name][name]['feature_importance'] = dict(zip(feature_cols, model.feature_importances_))

            print(f"       Train Accuracy: {results[decision_name][name]['train_accuracy']:.3f}")
            print(f"       Test Accuracy: {results[decision_name][name]['test_accuracy']:.3f}")
            print(f"       Test Precision: {results[decision_name][name]['test_precision']:.3f}")
            print(f"       Test Recall: {results[decision_name][name]['test_recall']:.3f}")

    return results, df


def simulate_strategy(df, model_results, threshold=0.5):
    """Simulate incremental trading strategies from simple to complex."""
    print(f"\n📈 Simulating incremental trading strategies (threshold={threshold})...")

    # Get test data
    split_idx = int(len(df) * 0.7)
    test_df = df.iloc[split_idx:].copy()

    feature_cols = get_feature_columns()
    X_test = test_df[feature_cols]

    # Get predictions for both decisions
    results_ibit = model_results['IBIT_Overnight']
    results_spy = model_results['SPY_Day']

    # Use the best model for each decision (XGBoost if available, otherwise Random Forest)
    if HAS_XGBOOST and 'XGBoost' in results_ibit:
        ibit_model_name = 'XGBoost'
        spy_model_name = 'XGBoost'
    else:
        ibit_model_name = 'Random Forest'
        spy_model_name = 'Random Forest'

    ibit_model_data = results_ibit[ibit_model_name]
    spy_model_data = results_spy[spy_model_name]

    ibit_model = ibit_model_data['model']
    spy_model = spy_model_data['model']
    scaler = ibit_model_data['scaler']  # Same scaler for both

    X_test_scaled = scaler.transform(X_test)

    # Get predictions and probabilities
    ibit_probabilities = ibit_model.predict_proba(X_test_scaled)[:, 1]
    spy_probabilities = spy_model.predict_proba(X_test_scaled)[:, 1]

    # Apply threshold to get confident predictions
    ibit_confident = (ibit_probabilities > threshold).astype(int)
    spy_confident = (spy_probabilities > threshold).astype(int)

    # ============ STRATEGY 1: Buy & Hold IBIT ============
    # Just hold IBIT every day - no trading
    test_df['buy_hold_ibit_return'] = test_df['ibit_hold_return']
    test_df['buy_hold_ibit_cumulative'] = (1 + test_df['buy_hold_ibit_return']).cumprod()

    # ============ STRATEGY 2: IBIT Night Only ============
    # Always rotate IBIT overnight, hold IBIT during day
    # This means: buy IBIT at close, sell at open (overnight return), then hold IBIT during day
    # So the return is just the overnight return (since we hold IBIT during day)
    test_df['ibit_night_only_return'] = test_df['ibit_overnight_return']
    test_df['ibit_night_only_cumulative'] = (1 + test_df['ibit_night_only_return']).cumprod()

    # ============ STRATEGY 3: ML IBIT Night Only ============
    # ML decides whether to rotate IBIT overnight or hold IBIT
    test_df['ml_ibit_night_signal'] = ibit_confident
    test_df['ml_ibit_night_only_return'] = np.where(
        test_df['ml_ibit_night_signal'] == 1,
        test_df['ibit_overnight_return'],  # Rotate: get overnight return
        test_df['ibit_hold_return']        # Hold: get hold return
    )
    test_df['ml_ibit_night_only_cumulative'] = (1 + test_df['ml_ibit_night_only_return']).cumprod()

    # ============ STRATEGY 4: ML Dual (IBIT Night + SPY Day) ============
    # ML decides both IBIT night rotation AND SPY day trading independently
    # If IBIT night signal = 1: rotate IBIT overnight, then trade SPY during day
    # If IBIT night signal = 0: hold IBIT overnight, hold IBIT during day
    # The SPY day decision is independent but only applies when doing rotation
    test_df['ml_dual_ibit_signal'] = ibit_confident
    test_df['ml_dual_spy_signal'] = spy_confident

    # For dual strategy: if IBIT signal is 1 AND SPY signal is 1, do full rotation
    # If IBIT signal is 1 but SPY signal is 0, do IBIT rotation but hold cash during day (so just overnight return)
    # If IBIT signal is 0, hold IBIT (regardless of SPY signal)
    test_df['ml_dual_return'] = np.where(
        test_df['ml_dual_ibit_signal'] == 1,
        np.where(
            test_df['ml_dual_spy_signal'] == 1,
            test_df['rotation_return'],  # Full rotation: overnight + SPY day
            test_df['ibit_overnight_return']  # Partial rotation: overnight only
        ),
        test_df['ibit_hold_return']  # Hold IBIT
    )
    test_df['ml_dual_cumulative'] = (1 + test_df['ml_dual_return']).cumprod()

    # Calculate performance metrics
    strategies = {
        'Buy & Hold IBIT': test_df['buy_hold_ibit_cumulative'],
        'IBIT Night Only': test_df['ibit_night_only_cumulative'],
        'ML IBIT Night Only': test_df['ml_ibit_night_only_cumulative'],
        'ML Dual (IBIT+SPY)': test_df['ml_dual_cumulative']
    }

    print("\nStrategy Performance:")
    for name, cumulative in strategies.items():
        total_return = cumulative.iloc[-1] - 1
        print(f"   {name}: {total_return:.1%}")

    print("\nIncremental Improvement:")
    base_return = strategies['Buy & Hold IBIT'].iloc[-1] - 1
    for name, cumulative in list(strategies.items())[1:]:
        total_return = cumulative.iloc[-1] - 1
        improvement = total_return - base_return
        print(f"   {name} vs Buy & Hold: {improvement:+.1%}")

    # Signal statistics
    ibit_signals = test_df['ml_ibit_night_signal'].sum()
    spy_signals = test_df['ml_dual_spy_signal'].sum()
    dual_signals = (test_df['ml_dual_ibit_signal'] & test_df['ml_dual_spy_signal']).sum()
    total_days = len(test_df)

    print("\nSignal Statistics:")
    print(f"   ML IBIT Night signals: {ibit_signals}/{total_days} days ({ibit_signals/total_days:.1%})")
    print(f"   ML SPY Day signals: {spy_signals}/{total_days} days ({spy_signals/total_days:.1%})")
    print(f"   ML Dual signals (both): {dual_signals}/{total_days} days ({dual_signals/total_days:.1%})")

    return test_df, ibit_model_name, spy_model_name


def plot_model_comparison(model_results):
    """Plot model performance comparison for both decisions."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    decisions = ['IBIT_Overnight', 'SPY_Day']
    metrics = ['test_accuracy', 'test_precision', 'test_recall', 'test_f1']

    for i, metric in enumerate(metrics):
        ax = axes[i//2, i%2]

        # Plot both decisions
        ibit_values = [model_results['IBIT_Overnight'][model][metric] for model in model_results['IBIT_Overnight'].keys()]
        spy_values = [model_results['SPY_Day'][model][metric] for model in model_results['SPY_Day'].keys()]
        models = list(model_results['IBIT_Overnight'].keys())

        x = np.arange(len(models))
        width = 0.35

        bars1 = ax.bar(x - width/2, ibit_values, width, label='IBIT Overnight', color='#2E86AB', alpha=0.8)
        bars2 = ax.bar(x + width/2, spy_values, width, label='SPY Day', color='#A23B72', alpha=0.8)

        ax.set_title(f'{metric.replace("_", " ").title()}', fontsize=12, fontweight='bold')
        ax.set_ylabel('Score', fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels(models, rotation=45, ha='right')
        ax.set_ylim(0, 1)
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Add value labels
        for bars, values in [(bars1, ibit_values), (bars2, spy_values)]:
            for bar, value in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height() + 0.01,
                       f'{value:.3f}', ha='center', va='bottom', fontsize=8)

    plt.suptitle('ML Model Performance Comparison - Dual Rotation Decisions', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'model_comparison.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {os.path.join(OUTPUT_DIR, 'model_comparison.png')}")


def plot_feature_importance(model_results):
    """Plot feature importance for both decisions."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    decisions = [('IBIT_Overnight', 'IBIT Overnight Return'), ('SPY_Day', 'SPY Day Return')]

    for i, (decision_key, title) in enumerate(decisions):
        ax = axes[i]

        # Use XGBoost if available, otherwise Random Forest
        if HAS_XGBOOST and 'XGBoost' in model_results[decision_key]:
            model_name = 'XGBoost'
        else:
            model_name = 'Random Forest'

        if model_results[decision_key][model_name]['feature_importance'] is None:
            ax.text(0.5, 0.5, f'No feature importance\navailable for {title}',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title(f'{title} - Feature Importance', fontsize=14, fontweight='bold')
            continue

        importance_dict = model_results[decision_key][model_name]['feature_importance']
        features = list(importance_dict.keys())
        importance = list(importance_dict.values())

        # Sort by importance
        sorted_idx = np.argsort(importance)[::-1]
        features_sorted = [features[i] for i in sorted_idx[:15]]  # Top 15
        importance_sorted = [importance[i] for i in sorted_idx[:15]]

        bars = ax.barh(range(len(features_sorted)), importance_sorted, color='#2E86AB')
        ax.set_yticks(range(len(features_sorted)))
        ax.set_yticklabels(features_sorted)
        ax.set_xlabel('Feature Importance', fontsize=12)
        ax.set_title(f'{title} - Top 15 Features ({model_name})', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

    plt.suptitle('Feature Importance Analysis - Dual ML Decisions', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'feature_importance.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {os.path.join(OUTPUT_DIR, 'feature_importance.png')}")


def plot_strategy_comparison(test_df):
    """Plot cumulative performance comparison for all four strategies."""
    fig, ax = plt.subplots(figsize=(14, 8))

    ax.plot(test_df.index, test_df['buy_hold_ibit_cumulative'], label='Buy & Hold IBIT',
            linewidth=2, color='#2E86AB')
    ax.plot(test_df.index, test_df['ibit_night_only_cumulative'], label='IBIT Night Only',
            linewidth=2, color='#A23B72')
    ax.plot(test_df.index, test_df['ml_ibit_night_only_cumulative'], label='ML IBIT Night Only',
            linewidth=2, color='#F18F01')
    ax.plot(test_df.index, test_df['ml_dual_cumulative'], label='ML Dual (IBIT+SPY)',
            linewidth=2, color='#FCCA46')

    ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
    ax.set_title('Incremental Strategy Performance Comparison', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3)

    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.2f}'))

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'strategy_comparison.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {os.path.join(OUTPUT_DIR, 'strategy_comparison.png')}")


def plot_shap_analysis(model_results, df):
    """Generate SHAP analysis for both decisions."""
    if not HAS_SHAP:
        print("SHAP not available, skipping analysis")
        return

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    decisions = [('IBIT_Overnight', 'IBIT Overnight Return'), ('SPY_Day', 'SPY Day Return')]

    for i, (decision_key, title) in enumerate(decisions):
        ax = axes[i]

        # Use XGBoost if available, otherwise Random Forest
        if HAS_XGBOOST and 'XGBoost' in model_results[decision_key]:
            model_name = 'XGBoost'
        else:
            model_name = 'Random Forest'

        model_data = model_results[decision_key][model_name]
        model = model_data['model']
        scaler = model_data['scaler']
        X_test = model_data['X_test']

        # Use a sample of test data for SHAP
        sample_size = min(100, len(X_test))
        X_sample = X_test.sample(n=sample_size, random_state=42)
        X_sample_scaled = scaler.transform(X_sample)

        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_sample_scaled)

            # Create a temporary figure for this subplot
            plt.figure(figsize=(8, 6))
            shap.summary_plot(shap_values, X_sample, feature_names=X_sample.columns,
                             show=False, max_display=15)
            plt.title(f'SHAP Feature Impact - {title} ({model_name})', fontsize=12, fontweight='bold')
            plt.tight_layout()

            # Save individual plots
            plt.savefig(os.path.join(OUTPUT_DIR, f'shap_{decision_key.lower()}.png'), dpi=150, bbox_inches='tight')
            plt.close()

            print(f"Saved: {os.path.join(OUTPUT_DIR, f'shap_{decision_key.lower()}.png')}")

        except Exception as e:
            print(f"SHAP analysis failed for {decision_key}: {e}")
            # Create empty plot
            ax.text(0.5, 0.5, f'SHAP analysis\nfailed for {title}',
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)

    # Create combined SHAP plot
    try:
        # Use IBIT decision for main SHAP plot
        model_data = model_results['IBIT_Overnight']
        if HAS_XGBOOST and 'XGBoost' in model_data:
            model_name = 'XGBoost'
        else:
            model_name = 'Random Forest'

        model = model_data[model_name]['model']
        scaler = model_data[model_name]['scaler']
        X_test = model_data[model_name]['X_test']

        sample_size = min(100, len(X_test))
        X_sample = X_test.sample(n=sample_size, random_state=42)
        X_sample_scaled = scaler.transform(X_sample)

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample_scaled)

        plt.figure(figsize=(12, 8))
        shap.summary_plot(shap_values, X_sample, feature_names=X_sample.columns,
                         show=False, max_display=20)
        plt.title(f'SHAP Feature Importance - Dual ML Decisions (IBIT Focus)', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, 'shap_summary.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {os.path.join(OUTPUT_DIR, 'shap_summary.png')}")

    except Exception as e:
        print(f"Combined SHAP analysis failed: {e}")


def generate_pdf_report(model_results, test_df, df):
    """Generate comprehensive PDF report for dual ML decisions."""
    pdf_path = os.path.join(OUTPUT_DIR, 'ml_rotation_strategy_report.pdf')
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2E86AB')
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#333333')
    )

    story = []

    # Title
    story.append(Paragraph("ML-Enhanced IBIT+SPY Rotation Strategy Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Paragraph(f"Training Period: {df.index[0].date()} to {df.index[int(len(df)*0.7)].date()}", styles['Normal']))
    story.append(Paragraph(f"Test Period: {df.index[int(len(df)*0.7)].date()} to {df.index[-1].date()}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Strategy Description
    story.append(Paragraph("Strategy Overview", heading_style))
    strategy_text = """
    <b>Incremental Strategy Development:</b><br/>
    1. <b>Buy & Hold IBIT:</b> Traditional buy-and-hold approach<br/>
    2. <b>IBIT Night Only:</b> Always rotate IBIT overnight (buy close, sell open), hold IBIT during day<br/>
    3. <b>ML IBIT Night Only:</b> ML decides whether to rotate IBIT overnight or hold IBIT<br/>
    4. <b>ML Dual (IBIT+SPY):</b> ML independently decides IBIT night rotation AND SPY day trading<br/>
    <br/>
    <b>Decision Point:</b> 3:50 PM - use intraday data to predict return directions
    """
    story.append(Paragraph(strategy_text, styles['Normal']))
    story.append(Spacer(1, 20))

    # Model Performance Tables
    decisions = [('IBIT_Overnight', 'IBIT Overnight Return Prediction'),
                 ('SPY_Day', 'SPY Day Return Prediction')]

    for decision_key, decision_title in decisions:
        story.append(Paragraph(f"ML Model Performance - {decision_title}", heading_style))

        model_data = []
        model_data.append(['Model', 'Accuracy', 'Precision', 'Recall', 'F1-Score'])

        for model_name in model_results[decision_key].keys():
            metrics = model_results[decision_key][model_name]
            model_data.append([
                model_name,
                f"{metrics['test_accuracy']:.3f}",
                f"{metrics['test_precision']:.3f}",
                f"{metrics['test_recall']:.3f}",
                f"{metrics['test_f1']:.3f}"
            ])

        model_table = Table(model_data, colWidths=[1.8*inch, 1.0*inch, 1.0*inch, 1.0*inch, 1.0*inch])
        model_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F5F5F5'), colors.HexColor('#EAEAEA')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        story.append(model_table)
        story.append(Spacer(1, 20))

    # Strategy Performance
    story.append(Paragraph("Incremental Strategy Performance Comparison", heading_style))

    strategies_perf = {
        'Buy & Hold IBIT': test_df['buy_hold_ibit_cumulative'],
        'IBIT Night Only': test_df['ibit_night_only_cumulative'],
        'ML IBIT Night Only': test_df['ml_ibit_night_only_cumulative'],
        'ML Dual (IBIT+SPY)': test_df['ml_dual_cumulative']
    }

    perf_data = [['Strategy', 'Total Return', 'Win Rate', 'Description']]
    base_return = strategies_perf['Buy & Hold IBIT'].iloc[-1] - 1

    for name, cumulative in strategies_perf.items():
        total_return = cumulative.iloc[-1] - 1

        if name == 'Buy & Hold IBIT':
            description = 'Hold IBIT every day'
            win_rate = f"{(test_df['ibit_hold_return'] > 0).mean():.1%}"
        elif name == 'IBIT Night Only':
            description = 'Always rotate IBIT overnight'
            win_rate = f"{(test_df['ibit_night_only_return'] > 0).mean():.1%}"
        elif name == 'ML IBIT Night Only':
            signal_rate = test_df['ml_ibit_night_signal'].mean()
            description = f'ML decides IBIT night ({signal_rate:.0%} signals)'
            win_rate = f"{(test_df['ml_ibit_night_only_return'] > 0).mean():.1%}"
        else:  # ML Dual
            signal_rate = (test_df['ml_dual_ibit_signal'] & test_df['ml_dual_spy_signal']).mean()
            description = f'ML decides both ({signal_rate:.0%} dual signals)'
            win_rate = f"{(test_df['ml_dual_return'] > 0).mean():.1%}"

        perf_data.append([
            name,
            f"{total_return:.1%}",
            win_rate,
            description
        ])

    perf_table = Table(perf_data, colWidths=[2.0*inch, 1.2*inch, 1.0*inch, 2.8*inch])
    perf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F5F5F5'), colors.HexColor('#EAEAEA')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('ALIGN', (3, 1), (-1, -1), 'LEFT'),  # Left align descriptions
    ]))
    story.append(perf_table)
    story.append(Spacer(1, 20))

    # ML Decision Statistics
    story.append(Paragraph("ML Decision Analysis", heading_style))

    ibit_signal_rate = test_df['ml_ibit_night_signal'].mean()
    spy_signal_rate = test_df['ml_dual_spy_signal'].mean()
    both_signals_rate = (test_df['ml_dual_ibit_signal'] & test_df['ml_dual_spy_signal']).mean()

    decision_data = [['Decision', 'Signal Rate', 'When Correct', 'When Wrong']]
    decision_data.append([
        'IBIT Overnight Buy',
        f"{ibit_signal_rate:.1%}",
        f"{(test_df[test_df['ml_ibit_night_signal'] == test_df['target_ibit_overnight']]['ibit_overnight_return'] > 0).mean():.1%}",
        f"{(test_df[test_df['ml_ibit_night_signal'] != test_df['target_ibit_overnight']]['ibit_overnight_return'] > 0).mean():.1%}"
    ])
    decision_data.append([
        'SPY Day Buy',
        f"{spy_signal_rate:.1%}",
        f"{(test_df[test_df['ml_dual_spy_signal'] == test_df['target_spy_day']]['spy_day_return'] > 0).mean():.1%}",
        f"{(test_df[test_df['ml_dual_spy_signal'] != test_df['target_spy_day']]['spy_day_return'] > 0).mean():.1%}"
    ])
    decision_data.append([
        'Both Decisions (Dual)',
        f"{both_signals_rate:.1%}",
        f"{(test_df[(test_df['ml_dual_ibit_signal'] == 1) & (test_df['ml_dual_spy_signal'] == 1)]['rotation_return'] > 0).mean():.1%}",
        f"{(test_df[(test_df['ml_dual_ibit_signal'] == 0) | (test_df['ml_dual_spy_signal'] == 0)]['ibit_hold_return'] > 0).mean():.1%}"
    ])
    decision_table = Table(decision_data, colWidths=[1.8*inch, 1.0*inch, 1.2*inch, 1.2*inch])
    decision_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F5F5F5'), colors.HexColor('#EAEAEA')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]))
    story.append(decision_table)
    story.append(Spacer(1, 30))

    # Page break before charts
    story.append(PageBreak())

    # Charts
    story.append(Paragraph("Performance Analysis", heading_style))
    story.append(Spacer(1, 10))

    # Model comparison chart
    img_path = os.path.join(OUTPUT_DIR, 'model_comparison.png')
    if os.path.exists(img_path):
        story.append(Paragraph("ML Model Performance Comparison", styles['Normal']))
        img = Image(img_path, width=7*inch, height=4*inch)
        story.append(img)
        story.append(Spacer(1, 20))

    # Strategy comparison chart
    img_path = os.path.join(OUTPUT_DIR, 'strategy_comparison.png')
    if os.path.exists(img_path):
        story.append(Paragraph("Strategy Performance Comparison", styles['Normal']))
        img = Image(img_path, width=7*inch, height=4*inch)
        story.append(img)

    story.append(PageBreak())

    # Feature importance
    img_path = os.path.join(OUTPUT_DIR, 'feature_importance.png')
    if os.path.exists(img_path):
        story.append(Paragraph("Feature Importance Analysis", styles['Normal']))
        img = Image(img_path, width=7*inch, height=4.5*inch)
        story.append(img)

    # SHAP analysis
    img_path = os.path.join(OUTPUT_DIR, 'shap_summary.png')
    if os.path.exists(img_path):
        story.append(PageBreak())
        story.append(Paragraph("SHAP Feature Impact Analysis", styles['Normal']))
        img = Image(img_path, width=7*inch, height=4.5*inch)
        story.append(img)

    # Build PDF
    doc.build(story)
    print(f"📄 PDF Report saved: {pdf_path}")
    return pdf_path


def main():
    """Run the complete ML rotation strategy analysis."""
    print("="*70)
    print("ML-ENHANCED IBIT+SPY ROTATION STRATEGY ANALYSIS")
    print("="*70)

    # Fetch data
    ibit_df, spy_df = fetch_data()

    # Create features
    df = create_features(ibit_df, spy_df)

    # Train models
    model_results, df = train_models(df)

    # Simulate strategy
    test_df, ibit_model_name, spy_model_name = simulate_strategy(df, model_results)

    # Generate visualizations
    print("\n📈 Generating visualizations...")
    plot_model_comparison(model_results)
    plot_feature_importance(model_results)
    plot_strategy_comparison(test_df)

    if HAS_SHAP:
        plot_shap_analysis(model_results, df)

    # Generate PDF report
    print("\n📄 Generating PDF report...")
    generate_pdf_report(model_results, test_df, df)

    # Save results
    test_df.to_csv(os.path.join(OUTPUT_DIR, 'ml_strategy_results.csv'))

    print(f"\n✅ ML Analysis complete! Results saved to: {OUTPUT_DIR}")
    print(f"   IBIT Model: {ibit_model_name}")
    print(f"   SPY Model: {spy_model_name}")

    return model_results, test_df, df


if __name__ == "__main__":
    model_results, test_df, df = main()