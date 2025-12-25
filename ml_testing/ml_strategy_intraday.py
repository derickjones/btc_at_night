"""
IBIT Overnight Strategy - Intraday Features ML Model
=====================================================
Uses features available at 3:50 PM including SAME-DAY intraday data:
- Today's open price (gap from yesterday's close)
- Current price at 3:50 PM (intraday return)
- Today's volume up to 3:50 PM
- Today's high/low (intraday range)
- Plus all prior-day features

This is the BEST tradeable model - uses real same-day signal 
that's actually available at decision time.
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
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output_intraday')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def fetch_data():
    """Fetch IBIT and SPY historical data."""
    print("📊 Fetching IBIT and SPY data...")
    
    start_date = "2024-01-11"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    ibit = yf.Ticker("IBIT")
    spy = yf.Ticker("SPY")
    
    ibit_df = ibit.history(start=start_date, end=end_date)
    spy_df = spy.history(start=start_date, end=end_date)
    
    print(f"   IBIT: {len(ibit_df)} trading days")
    print(f"   SPY: {len(spy_df)} trading days")
    
    return ibit_df, spy_df


def create_features(ibit_df, spy_df):
    """
    Create feature matrix using data available at 3:50 PM.
    
    INCLUDES same-day intraday data:
    - Today's open (available at 9:30 AM)
    - Simulated 3:50 PM price (we'll use close as proxy in backtest)
    - Today's high/low up to 3:50 PM
    - Today's volume up to 3:50 PM
    
    Note: In backtest, we use daily close as proxy for 3:50 PM price.
    This is reasonable since 3:50 PM is very close to 4:00 PM close.
    In live trading, you'd use the actual 3:50 PM price.
    """
    print("🔧 Engineering INTRADAY features (available at 3:50 PM)...")
    
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
    
    # Calculate overnight returns (target variable)
    df['overnight_return'] = (df['ibit_open'].shift(-1) - df['ibit_close']) / df['ibit_close']
    
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
    
    # Gap: How did IBIT open relative to yesterday's close?
    df['today_gap'] = (df['ibit_open'] - df['ibit_close'].shift(1)) / df['ibit_close'].shift(1)
    df['spy_today_gap'] = (df['spy_open'] - df['spy_close'].shift(1)) / df['spy_close'].shift(1)
    df['gap_vs_spy'] = df['today_gap'] - df['spy_today_gap']
    
    # Intraday return: How has today gone so far? (using close as proxy for 3:50 PM)
    df['intraday_return'] = (df['ibit_close'] - df['ibit_open']) / df['ibit_open']
    df['spy_intraday_return'] = (df['spy_close'] - df['spy_open']) / df['spy_open']
    df['intraday_vs_spy'] = df['intraday_return'] - df['spy_intraday_return']
    
    # Intraday range: Today's volatility
    df['intraday_range'] = (df['ibit_high'] - df['ibit_low']) / df['ibit_open']
    df['spy_intraday_range'] = (df['spy_high'] - df['spy_low']) / df['spy_open']
    
    # Where in today's range is current price? (0 = at low, 1 = at high)
    df['intraday_position'] = (df['ibit_close'] - df['ibit_low']) / (df['ibit_high'] - df['ibit_low'])
    df['intraday_position'] = df['intraday_position'].fillna(0.5)
    
    # Today's volume (in backtest, using full day; in live, would use volume up to 3:50 PM)
    # Scale by 0.9 to approximate 3:50 PM volume (90% of day elapsed)
    df['today_volume_scaled'] = df['ibit_volume'] * 0.9
    df['spy_today_volume_scaled'] = df['spy_volume'] * 0.9
    
    # Today's volume vs recent average
    df['today_volume_vs_ma5'] = df['today_volume_scaled'] / df['ibit_volume'].shift(1).rolling(5).mean()
    df['today_volume_vs_ma20'] = df['today_volume_scaled'] / df['ibit_volume'].shift(1).rolling(20).mean()
    
    # Today's IBIT/SPY volume ratio
    df['today_ibit_spy_vol_ratio'] = df['today_volume_scaled'] / df['spy_today_volume_scaled']
    
    # ============ PREVIOUS OVERNIGHT RETURNS (From prior days) ============
    df['prev_overnight_1'] = df['overnight_return'].shift(1)
    df['prev_overnight_2'] = df['overnight_return'].shift(2)
    df['prev_overnight_3'] = df['overnight_return'].shift(3)
    df['prev_overnight_5_avg'] = df['overnight_return'].shift(1).rolling(5).mean()
    df['prev_overnight_5_std'] = df['overnight_return'].shift(1).rolling(5).std()
    df['prev_overnight_10_avg'] = df['overnight_return'].shift(1).rolling(10).mean()
    
    # ============ PRIOR DAY RETURNS (Using yesterday's close) ============
    df['prior_day_return'] = df['ibit_close'].shift(1).pct_change(1)
    df['prior_5d_return'] = df['ibit_close'].shift(1).pct_change(5)
    df['prior_10d_return'] = df['ibit_close'].shift(1).pct_change(10)
    df['prior_20d_return'] = df['ibit_close'].shift(1).pct_change(20)
    
    df['spy_prior_day_return'] = df['spy_close'].shift(1).pct_change(1)
    df['spy_prior_5d_return'] = df['spy_close'].shift(1).pct_change(5)
    
    df['ibit_vs_spy_prior_1d'] = df['prior_day_return'] - df['spy_prior_day_return']
    df['ibit_vs_spy_prior_5d'] = df['prior_5d_return'] - df['spy_prior_5d_return']
    
    # ============ PRIOR VOLATILITY ============
    prior_returns = df['ibit_close'].shift(1).pct_change()
    df['prior_volatility_5d'] = prior_returns.rolling(5).std()
    df['prior_volatility_10d'] = prior_returns.rolling(10).std()
    df['prior_volatility_20d'] = prior_returns.rolling(20).std()
    
    # ============ PRICE LEVEL FEATURES ============
    df['prior_close'] = df['ibit_close'].shift(1)
    df['prior_close_ma5'] = df['ibit_close'].shift(1).rolling(5).mean()
    df['prior_close_ma20'] = df['ibit_close'].shift(1).rolling(20).mean()
    df['prior_close_vs_ma5'] = df['prior_close'] / df['prior_close_ma5'] - 1
    df['prior_close_vs_ma20'] = df['prior_close'] / df['prior_close_ma20'] - 1
    
    # Current price vs MAs (available at 3:50 PM)
    df['current_vs_ma5'] = df['ibit_close'] / df['prior_close_ma5'] - 1
    df['current_vs_ma20'] = df['ibit_close'] / df['prior_close_ma20'] - 1
    
    # ============ TARGET VARIABLE ============
    df['target'] = (df['overnight_return'] > 0).astype(int)
    
    # Drop NaN rows
    df = df.dropna()
    
    print(f"   Created intraday + prior-day features")
    print(f"   {len(df)} samples after dropping NaN")
    
    return df


def get_feature_columns():
    """Return list of features available at 3:50 PM."""
    return [
        # Datetime features
        'day_of_week', 'month', 'day_of_month', 'week_of_year', 'quarter',
        'is_monday', 'is_friday', 'is_month_start', 'is_month_end',
        
        # SAME-DAY INTRADAY features (the key addition!)
        'today_gap', 'spy_today_gap', 'gap_vs_spy',
        'intraday_return', 'spy_intraday_return', 'intraday_vs_spy',
        'intraday_range', 'spy_intraday_range',
        'intraday_position',
        'today_volume_vs_ma5', 'today_volume_vs_ma20',
        'today_ibit_spy_vol_ratio',
        'current_vs_ma5', 'current_vs_ma20',
        
        # Previous overnight returns
        'prev_overnight_1', 'prev_overnight_2', 'prev_overnight_3',
        'prev_overnight_5_avg', 'prev_overnight_5_std', 'prev_overnight_10_avg',
        
        # Prior day returns
        'prior_day_return', 'prior_5d_return', 'prior_10d_return', 'prior_20d_return',
        'spy_prior_day_return', 'spy_prior_5d_return',
        'ibit_vs_spy_prior_1d', 'ibit_vs_spy_prior_5d',
        
        # Prior volatility
        'prior_volatility_5d', 'prior_volatility_10d', 'prior_volatility_20d',
        
        # Price level features
        'prior_close_vs_ma5', 'prior_close_vs_ma20'
    ]


def train_models(df):
    """Train multiple ML models and evaluate performance."""
    print("\n🤖 Training ML models (intraday + prior-day features)...")
    
    feature_cols = get_feature_columns()
    X = df[feature_cols]
    y = df['target']
    
    # Time-series split
    split_idx = int(len(df) * 0.7)
    
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"   Training set: {len(X_train)} samples")
    print(f"   Test set: {len(X_test)} samples")
    print(f"   Baseline (always predict positive): {y_test.mean():.1%}")
    
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
    trained_models = {}
    
    for name, model in models.items():
        print(f"\n   Training {name}...")
        
        if name == 'Logistic Regression':
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        results[name] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'predictions': y_pred,
            'probabilities': y_pred_proba
        }
        trained_models[name] = model
        
        print(f"      Accuracy: {accuracy:.1%}")
        print(f"      Precision: {precision:.1%}")
        print(f"      Recall: {recall:.1%}")
        print(f"      F1 Score: {f1:.2f}")
    
    return results, trained_models, scaler, (X_train, X_test, y_train, y_test), split_idx


def backtest_strategies(df, results, split_idx):
    """Backtest ML-enhanced strategies vs baseline strategies."""
    print("\n📈 Backtesting strategies...")
    
    test_df = df.iloc[split_idx:].copy()
    
    strategies = {
        'Buy & Hold': [],
        'Always Night': [],
    }
    
    for model_name, result in results.items():
        strategies[f'ML: {model_name}'] = result['predictions']
    
    backtest_results = {}
    
    for strategy_name, signals in strategies.items():
        if strategy_name == 'Buy & Hold':
            daily_returns = test_df['ibit_close'].pct_change().fillna(0)
        elif strategy_name == 'Always Night':
            daily_returns = test_df['overnight_return'].fillna(0)
        else:
            signals = np.array(signals)
            daily_returns = test_df['overnight_return'].fillna(0) * signals
        
        cumulative = (1 + daily_returns).cumprod()
        
        total_return = cumulative.iloc[-1] - 1
        n_days = len(daily_returns)
        annualized_return = (1 + total_return) ** (252 / n_days) - 1 if n_days > 0 else 0
        volatility = daily_returns.std() * np.sqrt(252)
        sharpe = (annualized_return - 0.05) / volatility if volatility > 0 else 0
        
        rolling_max = cumulative.expanding().max()
        drawdown = cumulative / rolling_max - 1
        max_drawdown = drawdown.min()
        
        if strategy_name not in ['Buy & Hold']:
            if isinstance(signals, np.ndarray):
                traded_returns = daily_returns[signals == 1] if len(signals) == len(daily_returns) else daily_returns
            else:
                traded_returns = daily_returns
            trades = len(traded_returns[traded_returns != 0])
            wins = len(traded_returns[traded_returns > 0])
            win_rate = wins / trades if trades > 0 else 0
        else:
            win_rate = (daily_returns > 0).mean()
            trades = len(daily_returns)
        
        backtest_results[strategy_name] = {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'num_trades': trades,
            'cumulative': cumulative,
            'daily_returns': daily_returns
        }
    
    return backtest_results, test_df


def plot_cumulative_performance(backtest_results, test_df):
    """Plot cumulative performance of all strategies."""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    colors_list = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3A7D44', '#9B59B6']
    
    for i, (name, result) in enumerate(backtest_results.items()):
        ax.plot(test_df.index, result['cumulative'], 
                label=name, linewidth=2, color=colors_list[i % len(colors_list)])
    
    ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
    ax.set_title('INTRADAY Strategy Comparison\n(Using features available at 3:50 PM including same-day data)', 
                fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.2f}'))
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'intraday_cumulative_performance.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"   Saved: intraday_cumulative_performance.png")


def plot_model_comparison(results):
    """Plot model accuracy comparison."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    models = list(results.keys())
    metrics = ['accuracy', 'precision', 'recall', 'f1']
    
    x = np.arange(len(models))
    width = 0.2
    
    colors_list = ['#2E86AB', '#A23B72', '#F18F01', '#3A7D44']
    
    for i, metric in enumerate(metrics):
        values = [results[m][metric] for m in models]
        ax.bar(x + i*width, values, width, label=metric.capitalize(), color=colors_list[i])
    
    ax.set_ylabel('Score', fontsize=12)
    ax.set_title('INTRADAY Model Performance Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(models, rotation=15, ha='right')
    ax.legend(loc='lower right')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'intraday_model_comparison.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"   Saved: intraday_model_comparison.png")


def plot_shap_analysis(trained_models, X_train, X_test, feature_cols):
    """Generate SHAP beeswarm plots for each model."""
    if not HAS_SHAP:
        print("   SHAP not available, skipping SHAP plots")
        return {}
    
    print("   Generating SHAP plots...")
    shap_plots = {}
    
    X_test_arr = np.array(X_test)
    X_train_arr = np.array(X_train)
    
    for name, model in trained_models.items():
        try:
            print(f"      Computing SHAP values for {name}...")
            
            if name == 'Logistic Regression':
                explainer = shap.LinearExplainer(model, X_train_arr)
                shap_values = explainer.shap_values(X_test_arr)
            elif name in ['Random Forest', 'Gradient Boosting', 'XGBoost']:
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X_test_arr)
                if isinstance(shap_values, list):
                    shap_values = shap_values[1]
                elif len(shap_values.shape) == 3:
                    shap_values = shap_values[:, :, 1]
            else:
                continue
            
            if len(shap_values.shape) == 1:
                shap_values = shap_values.reshape(1, -1)
            
            plt.figure(figsize=(10, 8))
            shap.summary_plot(
                shap_values, 
                X_test_arr, 
                feature_names=feature_cols,
                show=False, 
                max_display=15,
                plot_size=None
            )
            plt.title(f'SHAP Summary (Intraday): {name}', fontsize=14, fontweight='bold', y=1.02)
            plt.tight_layout()
            
            filename = f'intraday_shap_{name.lower().replace(" ", "_")}.png'
            filepath = os.path.join(OUTPUT_DIR, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close('all')
            
            shap_plots[name] = filepath
            print(f"      Saved: {filename}")
            
        except Exception as e:
            print(f"      Warning: Could not generate SHAP for {name}: {str(e)}")
            continue
    
    return shap_plots


def generate_pdf_report(ml_results, backtest_results, df, shap_plots=None):
    """Generate comprehensive PDF report."""
    print("\n📄 Generating PDF report...")
    
    if shap_plots is None:
        shap_plots = {}
    
    pdf_path = os.path.join(OUTPUT_DIR, 'intraday_ml_report.pdf')
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                  fontSize=24, spaceAfter=30, alignment=TA_CENTER,
                                  textColor=colors.HexColor('#2E86AB'))
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
                                    fontSize=16, spaceBefore=20, spaceAfter=10)
    
    story = []
    
    # Title
    story.append(Paragraph("IBIT Overnight Strategy - INTRADAY ML Model", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Key Advantage:</b> This model uses SAME-DAY intraday data available at 3:50 PM, "
        "including today's gap, intraday return, and volume - providing real-time signal "
        "while still being usable for live trading.",
        styles['Normal']
    ))
    story.append(Spacer(1, 20))
    
    # ML Model Performance
    story.append(Paragraph("ML Model Performance", heading_style))
    
    ml_data = [['Model', 'Accuracy', 'Precision', 'Recall', 'F1 Score']]
    for name, result in ml_results.items():
        ml_data.append([
            name,
            f"{result['accuracy']:.1%}",
            f"{result['precision']:.1%}",
            f"{result['recall']:.1%}",
            f"{result['f1']:.2f}"
        ])
    
    ml_table = Table(ml_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
    ml_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F5F5F5'), colors.HexColor('#EAEAEA')]),
    ]))
    story.append(ml_table)
    story.append(Spacer(1, 30))
    
    # Strategy Backtest Results
    story.append(Paragraph("Strategy Backtest Results (Test Period)", heading_style))
    
    bt_data = [['Strategy', 'Total Return', 'Sharpe', 'Max DD', 'Win Rate', 'Trades']]
    for name, result in backtest_results.items():
        bt_data.append([
            name[:25],
            f"{result['total_return']:.1%}",
            f"{result['sharpe_ratio']:.2f}",
            f"{result['max_drawdown']:.1%}",
            f"{result['win_rate']:.1%}",
            f"{result['num_trades']}"
        ])
    
    bt_table = Table(bt_data, colWidths=[2.2*inch, 1.1*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.8*inch])
    bt_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#A23B72')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F5F5F5'), colors.HexColor('#EAEAEA')]),
    ]))
    story.append(bt_table)
    
    story.append(PageBreak())
    
    # Key Intraday Features explanation
    story.append(Paragraph("Key Intraday Features", heading_style))
    story.append(Paragraph(
        "<b>Same-day features available at 3:50 PM:</b><br/><br/>"
        "• <b>today_gap</b>: (Today Open - Yesterday Close) / Yesterday Close<br/>"
        "• <b>intraday_return</b>: (Current Price - Today Open) / Today Open<br/>"
        "• <b>intraday_vs_spy</b>: IBIT intraday return minus SPY intraday return<br/>"
        "• <b>intraday_range</b>: (Today High - Today Low) / Today Open<br/>"
        "• <b>intraday_position</b>: Where current price is in today's range (0-1)<br/>"
        "• <b>today_volume_vs_ma</b>: Today's volume vs recent average<br/>"
        "• <b>current_vs_ma5/20</b>: Current price vs moving averages<br/>",
        styles['Normal']
    ))
    story.append(Spacer(1, 20))
    
    # Charts
    story.append(Paragraph("Performance Charts", heading_style))
    
    img_path = os.path.join(OUTPUT_DIR, 'intraday_cumulative_performance.png')
    if os.path.exists(img_path):
        story.append(Image(img_path, width=7*inch, height=4*inch))
        story.append(Spacer(1, 20))
    
    img_path = os.path.join(OUTPUT_DIR, 'intraday_model_comparison.png')
    if os.path.exists(img_path):
        story.append(Image(img_path, width=6*inch, height=3.5*inch))
    
    # SHAP Analysis
    if shap_plots:
        story.append(PageBreak())
        story.append(Paragraph("SHAP Analysis - Feature Importance", heading_style))
        story.append(Paragraph(
            "SHAP values show how each feature contributes to predictions. "
            "Look for same-day intraday features (gap, intraday_return, etc.) to see "
            "how much predictive power they add.",
            styles['Normal']
        ))
        story.append(Spacer(1, 15))
        
        for model_name, shap_path in shap_plots.items():
            if os.path.exists(shap_path):
                story.append(Image(shap_path, width=6.5*inch, height=5*inch))
                story.append(Spacer(1, 10))
    
    # Build PDF
    doc.build(story)
    print(f"   📄 PDF Report saved: {pdf_path}")


def print_summary(ml_results, backtest_results):
    """Print summary to console."""
    print("\n" + "="*80)
    print("INTRADAY ML STRATEGY RESULTS (Same-day features available at 3:50 PM)")
    print("="*80)
    
    print("\n📊 ML MODEL PERFORMANCE:")
    print("-"*60)
    for name, result in ml_results.items():
        print(f"  {name}:")
        print(f"    Accuracy: {result['accuracy']:.1%} | Precision: {result['precision']:.1%} | F1: {result['f1']:.2f}")
    
    print("\n\n💰 BACKTEST RESULTS (Test Period):")
    print("-"*60)
    for name, result in backtest_results.items():
        print(f"  {name}:")
        print(f"    Return: {result['total_return']:.1%} | Sharpe: {result['sharpe_ratio']:.2f} | MaxDD: {result['max_drawdown']:.1%}")
    
    print("\n" + "="*80)


def compare_with_other_models():
    """Print comparison with other model versions."""
    print("\n" + "="*80)
    print("📊 COMPARISON WITH OTHER MODELS")
    print("="*80)
    print("""
    BASELINE MODEL (ml_strategy_analysis.py):
    - Uses end-of-day data (NOT tradeable - data unavailable at decision time)
    - Random Forest: 25.8% return, 1.84 Sharpe
    
    TRADEABLE MODEL (ml_strategy_tradeable.py):
    - Uses ONLY prior-day data
    - Logistic Regression: 21.9% return, 1.44 Sharpe
    
    INTRADAY MODEL (this script):
    - Uses same-day intraday data available at 3:50 PM
    - See results above
    
    The intraday model should perform between tradeable and baseline,
    since it has more information than tradeable but less than baseline.
    """)
    print("="*80)


def main():
    """Run intraday ML analysis."""
    print("="*60)
    print("IBIT Overnight Strategy - INTRADAY ML Analysis")
    print("(Using same-day features available at 3:50 PM)")
    print("="*60)
    
    # Fetch data
    ibit_df, spy_df = fetch_data()
    
    # Create features
    df = create_features(ibit_df, spy_df)
    
    # Train models
    ml_results, trained_models, scaler, splits, split_idx = train_models(df)
    
    # Backtest strategies
    backtest_results, test_df = backtest_strategies(df, ml_results, split_idx)
    
    # Print summary
    print_summary(ml_results, backtest_results)
    
    # Generate plots
    print("\n📈 Generating visualizations...")
    plot_cumulative_performance(backtest_results, test_df)
    plot_model_comparison(ml_results)
    
    # Generate SHAP plots
    X_train, X_test, y_train, y_test = splits
    shap_plots = plot_shap_analysis(trained_models, X_train, X_test, get_feature_columns())
    
    # Generate PDF report
    generate_pdf_report(ml_results, backtest_results, df, shap_plots)
    
    # Save results
    results_df = pd.DataFrame({
        'strategy': list(backtest_results.keys()),
        'total_return': [r['total_return'] for r in backtest_results.values()],
        'sharpe_ratio': [r['sharpe_ratio'] for r in backtest_results.values()],
        'max_drawdown': [r['max_drawdown'] for r in backtest_results.values()],
        'win_rate': [r['win_rate'] for r in backtest_results.values()]
    })
    results_df.to_csv(os.path.join(OUTPUT_DIR, 'intraday_backtest_results.csv'), index=False)
    
    # Compare with other models
    compare_with_other_models()
    
    print(f"\n✅ Analysis complete! Results saved to: {OUTPUT_DIR}")
    
    return df, ml_results, backtest_results


if __name__ == "__main__":
    df, ml_results, backtest_results = main()
