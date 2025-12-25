"""
IBIT Overnight Strategy - Machine Learning Enhancement
======================================================
Uses ML models to predict which nights are best for the overnight strategy.

Features:
- Day of week
- Month
- Day of month
- Week of year
- IBIT trading volume
- SPY trading volume
- Volume ratios and moving averages
- Recent performance indicators

Models tested:
- Random Forest Classifier
- Gradient Boosting Classifier
- Logistic Regression
- XGBoost (if available)
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
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except (ImportError, Exception):
    HAS_XGBOOST = False
    print("Note: XGBoost not available, using other models only")

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    print("Note: SHAP not available, skipping SHAP analysis")

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def fetch_data():
    """Fetch IBIT and SPY historical data."""
    print("📊 Fetching IBIT and SPY data...")
    
    # IBIT launched January 11, 2024
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
    """Create feature matrix for ML models."""
    print("🔧 Engineering features...")
    
    # Merge dataframes on date
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
    df['spy_close'] = spy_aligned['Close']
    df['spy_volume'] = spy_aligned['Volume']
    
    # Calculate overnight returns (target variable)
    df['overnight_return'] = (df['ibit_open'].shift(-1) - df['ibit_close']) / df['ibit_close']
    
    # Day returns
    df['ibit_day_return'] = (df['ibit_close'] - df['ibit_open']) / df['ibit_open']
    df['spy_day_return'] = (df['spy_close'] - df['spy_open']) / df['spy_open']
    
    # ============ DATETIME FEATURES ============
    df['day_of_week'] = df.index.dayofweek  # Monday=0, Friday=4
    df['month'] = df.index.month
    df['day_of_month'] = df.index.day
    df['week_of_year'] = df.index.isocalendar().week.astype(int)
    df['quarter'] = df.index.quarter
    
    # Is it Monday? (overnight from Friday)
    df['is_monday'] = (df['day_of_week'] == 0).astype(int)
    # Is it Friday? (weekend overnight coming)
    df['is_friday'] = (df['day_of_week'] == 4).astype(int)
    # Month start/end
    df['is_month_start'] = (df['day_of_month'] <= 5).astype(int)
    df['is_month_end'] = (df['day_of_month'] >= 25).astype(int)
    
    # ============ VOLUME FEATURES ============
    # Raw volumes (will be scaled)
    df['ibit_volume_raw'] = df['ibit_volume']
    df['spy_volume_raw'] = df['spy_volume']
    
    # Volume moving averages
    df['ibit_volume_ma5'] = df['ibit_volume'].rolling(5).mean()
    df['ibit_volume_ma20'] = df['ibit_volume'].rolling(20).mean()
    df['spy_volume_ma5'] = df['spy_volume'].rolling(5).mean()
    df['spy_volume_ma20'] = df['spy_volume'].rolling(20).mean()
    
    # Volume ratios (current vs average)
    df['ibit_volume_ratio_5'] = df['ibit_volume'] / df['ibit_volume_ma5']
    df['ibit_volume_ratio_20'] = df['ibit_volume'] / df['ibit_volume_ma20']
    df['spy_volume_ratio_5'] = df['spy_volume'] / df['spy_volume_ma5']
    df['spy_volume_ratio_20'] = df['spy_volume'] / df['spy_volume_ma20']
    
    # IBIT/SPY volume ratio
    df['ibit_spy_volume_ratio'] = df['ibit_volume'] / df['spy_volume']
    
    # ============ PRICE/MOMENTUM FEATURES ============
    # Recent performance
    df['ibit_return_1d'] = df['ibit_close'].pct_change(1)
    df['ibit_return_5d'] = df['ibit_close'].pct_change(5)
    df['ibit_return_10d'] = df['ibit_close'].pct_change(10)
    
    df['spy_return_1d'] = df['spy_close'].pct_change(1)
    df['spy_return_5d'] = df['spy_close'].pct_change(5)
    
    # Relative strength
    df['ibit_vs_spy_1d'] = df['ibit_return_1d'] - df['spy_return_1d']
    df['ibit_vs_spy_5d'] = df['ibit_return_5d'] - df['spy_return_5d']
    
    # Volatility (rolling std of returns)
    df['ibit_volatility_5d'] = df['ibit_return_1d'].rolling(5).std()
    df['ibit_volatility_20d'] = df['ibit_return_1d'].rolling(20).std()
    
    # Intraday range
    df['ibit_range'] = (df['ibit_high'] - df['ibit_low']) / df['ibit_close']
    
    # Previous overnight returns
    df['prev_overnight_1'] = df['overnight_return'].shift(1)
    df['prev_overnight_2'] = df['overnight_return'].shift(2)
    df['prev_overnight_5_avg'] = df['overnight_return'].shift(1).rolling(5).mean()
    
    # ============ TARGET VARIABLE ============
    # Binary classification: 1 if overnight return > 0, else 0
    df['target'] = (df['overnight_return'] > 0).astype(int)
    
    # Drop NaN rows
    df = df.dropna()
    
    print(f"   Created {len([c for c in df.columns if c not in ['overnight_return', 'target']])} features")
    print(f"   {len(df)} samples after dropping NaN")
    
    return df


def get_feature_columns():
    """Return list of feature columns for ML models."""
    return [
        # Datetime features
        'day_of_week', 'month', 'day_of_month', 'week_of_year', 'quarter',
        'is_monday', 'is_friday', 'is_month_start', 'is_month_end',
        
        # Volume features
        'ibit_volume_ratio_5', 'ibit_volume_ratio_20',
        'spy_volume_ratio_5', 'spy_volume_ratio_20',
        'ibit_spy_volume_ratio',
        
        # Price/momentum features
        'ibit_return_1d', 'ibit_return_5d', 'ibit_return_10d',
        'spy_return_1d', 'spy_return_5d',
        'ibit_vs_spy_1d', 'ibit_vs_spy_5d',
        'ibit_volatility_5d', 'ibit_volatility_20d',
        'ibit_range',
        'ibit_day_return', 'spy_day_return',
        
        # Previous overnight performance
        'prev_overnight_1', 'prev_overnight_2', 'prev_overnight_5_avg'
    ]


def train_models(df):
    """Train multiple ML models and evaluate performance."""
    print("\n🤖 Training ML models...")
    
    feature_cols = get_feature_columns()
    X = df[feature_cols]
    y = df['target']
    
    # Use time-series split (don't leak future data)
    # Train on first 70%, test on last 30%
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
    
    # Define models
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
        
        # Train
        if name == 'Logistic Regression':
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Metrics
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


def get_feature_importance(models, feature_cols):
    """Extract feature importance from tree-based models."""
    importance_dict = {}
    
    for name, model in models.items():
        if hasattr(model, 'feature_importances_'):
            importance_dict[name] = dict(zip(feature_cols, model.feature_importances_))
    
    return importance_dict


def backtest_strategies(df, results, split_idx):
    """Backtest ML-enhanced strategies vs baseline strategies."""
    print("\n📈 Backtesting strategies...")
    
    # Test period only
    test_df = df.iloc[split_idx:].copy()
    
    strategies = {
        'Buy & Hold': [],
        'Always Night': [],
    }
    
    # Add ML strategies
    for model_name, result in results.items():
        strategies[f'ML: {model_name}'] = result['predictions']
        # Also test high-confidence predictions (>60% probability)
        strategies[f'ML: {model_name} (>60%)'] = (result['probabilities'] > 0.6).astype(int)
    
    # Calculate returns for each strategy
    backtest_results = {}
    
    for strategy_name, signals in strategies.items():
        if strategy_name == 'Buy & Hold':
            # Hold IBIT continuously
            daily_returns = test_df['ibit_close'].pct_change().fillna(0)
        elif strategy_name == 'Always Night':
            # Always do overnight strategy
            daily_returns = test_df['overnight_return'].fillna(0)
        else:
            # ML-based: only trade when signal is 1
            signals = np.array(signals)
            daily_returns = test_df['overnight_return'].fillna(0) * signals
        
        cumulative = (1 + daily_returns).cumprod()
        
        total_return = cumulative.iloc[-1] - 1
        n_days = len(daily_returns)
        annualized_return = (1 + total_return) ** (252 / n_days) - 1 if n_days > 0 else 0
        volatility = daily_returns.std() * np.sqrt(252)
        sharpe = (annualized_return - 0.05) / volatility if volatility > 0 else 0
        
        # Calculate max drawdown
        rolling_max = cumulative.expanding().max()
        drawdown = cumulative / rolling_max - 1
        max_drawdown = drawdown.min()
        
        # Win rate (for strategies that trade)
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
    
    colors_list = ['#2E86AB', "#191417", '#F18F01', '#C73E1D', '#3A7D44', '#9B59B6', '#E74C3C', '#1ABC9C']
    
    for i, (name, result) in enumerate(backtest_results.items()):
        # Skip high-confidence variants for cleaner chart
        if '(>60%)' in name:
            continue
        ax.plot(test_df.index, result['cumulative'], 
                label=name, linewidth=2, color=colors_list[i % len(colors_list)])
    
    ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
    ax.set_title('Strategy Comparison: ML-Enhanced vs Baseline\n(Test Period)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.2f}'))
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'ml_cumulative_performance.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"   Saved: ml_cumulative_performance.png")


def plot_feature_importance(importance_dict):
    """Plot feature importance for each model."""
    n_models = len(importance_dict)
    if n_models == 0:
        return
    
    fig, axes = plt.subplots(1, n_models, figsize=(6*n_models, 8))
    if n_models == 1:
        axes = [axes]
    
    for ax, (model_name, importance) in zip(axes, importance_dict.items()):
        sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:15]
        features = [x[0] for x in sorted_importance]
        values = [x[1] for x in sorted_importance]
        
        ax.barh(features, values, color='#2E86AB')
        ax.set_xlabel('Importance', fontsize=10)
        ax.set_title(f'{model_name}\nTop 15 Features', fontsize=11, fontweight='bold')
        ax.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'ml_feature_importance.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"   Saved: ml_feature_importance.png")


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
    ax.set_title('ML Model Performance Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(models, rotation=15, ha='right')
    ax.legend(loc='lower right')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'ml_model_comparison.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"   Saved: ml_model_comparison.png")


def plot_shap_analysis(trained_models, X_train, X_test, feature_cols):
    """Generate SHAP beeswarm plots for each model."""
    if not HAS_SHAP:
        print("   SHAP not available, skipping SHAP plots")
        return {}
    
    print("   Generating SHAP plots...")
    shap_plots = {}
    
    # Convert to numpy arrays for SHAP compatibility
    X_test_arr = np.array(X_test)
    X_train_arr = np.array(X_train)
    
    for name, model in trained_models.items():
        try:
            print(f"      Computing SHAP values for {name}...")
            
            # Use appropriate explainer based on model type
            if name == 'Logistic Regression':
                explainer = shap.LinearExplainer(model, X_train_arr)
                shap_values = explainer.shap_values(X_test_arr)
            elif name in ['Random Forest', 'Gradient Boosting', 'XGBoost']:
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X_test_arr)
                # For binary classification, TreeExplainer may return list or 3D array
                if isinstance(shap_values, list):
                    shap_values = shap_values[1]  # Get positive class
                elif len(shap_values.shape) == 3:
                    shap_values = shap_values[:, :, 1]  # Get positive class from 3D array
            else:
                continue
            
            # Ensure 2D array
            if len(shap_values.shape) == 1:
                shap_values = shap_values.reshape(1, -1)
            
            # Create beeswarm plot
            plt.figure(figsize=(10, 8))
            shap.summary_plot(
                shap_values, 
                X_test_arr, 
                feature_names=feature_cols,
                show=False, 
                max_display=15,
                plot_size=None
            )
            plt.title(f'SHAP Summary: {name}', fontsize=14, fontweight='bold', y=1.02)
            plt.tight_layout()
            
            filename = f'shap_{name.lower().replace(" ", "_")}.png'
            filepath = os.path.join(OUTPUT_DIR, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close('all')
            
            shap_plots[name] = filepath
            print(f"      Saved: {filename}")
            
        except Exception as e:
            print(f"      Warning: Could not generate SHAP for {name}: {str(e)}")
            continue
    
    return shap_plots


def generate_pdf_report(ml_results, backtest_results, importance_dict, df, shap_plots=None):
    """Generate comprehensive PDF report."""
    print("\n📄 Generating PDF report...")
    
    if shap_plots is None:
        shap_plots = {}
    
    pdf_path = os.path.join(OUTPUT_DIR, 'ml_strategy_report.pdf')
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
    story.append(Paragraph("IBIT Overnight Strategy - ML Analysis", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
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
        if '(>60%)' in name:
            continue
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
    
    # Charts
    story.append(Paragraph("Performance Charts", heading_style))
    
    img_path = os.path.join(OUTPUT_DIR, 'ml_cumulative_performance.png')
    if os.path.exists(img_path):
        story.append(Image(img_path, width=7*inch, height=4*inch))
        story.append(Spacer(1, 20))
    
    img_path = os.path.join(OUTPUT_DIR, 'ml_model_comparison.png')
    if os.path.exists(img_path):
        story.append(Image(img_path, width=6*inch, height=3.5*inch))
    
    story.append(PageBreak())
    
    # Feature Importance
    story.append(Paragraph("Feature Importance Analysis", heading_style))
    
    img_path = os.path.join(OUTPUT_DIR, 'ml_feature_importance.png')
    if os.path.exists(img_path):
        story.append(Image(img_path, width=7.5*inch, height=5*inch))
    
    # SHAP Analysis
    if shap_plots:
        story.append(PageBreak())
        story.append(Paragraph("SHAP Analysis - Global Feature Importance", heading_style))
        story.append(Paragraph(
            "SHAP (SHapley Additive exPlanations) values quantify each feature's contribution to model predictions. "
            "Higher values indicate greater influence on the model's decision to predict positive overnight returns.",
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
    print("ML STRATEGY ANALYSIS RESULTS")
    print("="*80)
    
    print("\n📊 ML MODEL PERFORMANCE:")
    print("-"*60)
    for name, result in ml_results.items():
        print(f"  {name}:")
        print(f"    Accuracy: {result['accuracy']:.1%} | Precision: {result['precision']:.1%} | F1: {result['f1']:.2f}")
    
    print("\n\n💰 BACKTEST RESULTS (Test Period):")
    print("-"*60)
    for name, result in backtest_results.items():
        if '(>60%)' in name:
            continue
        print(f"  {name}:")
        print(f"    Return: {result['total_return']:.1%} | Sharpe: {result['sharpe_ratio']:.2f} | MaxDD: {result['max_drawdown']:.1%}")
    
    print("\n" + "="*80)


def main():
    """Run ML analysis."""
    print("="*60)
    print("IBIT Overnight Strategy - ML Analysis")
    print("="*60)
    
    # Fetch data
    ibit_df, spy_df = fetch_data()
    
    # Create features
    df = create_features(ibit_df, spy_df)
    
    # Train models
    ml_results, trained_models, scaler, splits, split_idx = train_models(df)
    
    # Get feature importance
    importance_dict = get_feature_importance(trained_models, get_feature_columns())
    
    # Backtest strategies
    backtest_results, test_df = backtest_strategies(df, ml_results, split_idx)
    
    # Print summary
    print_summary(ml_results, backtest_results)
    
    # Generate plots
    print("\n📈 Generating visualizations...")
    plot_cumulative_performance(backtest_results, test_df)
    plot_model_comparison(ml_results)
    plot_feature_importance(importance_dict)
    
    # Generate SHAP plots
    X_train, X_test, y_train, y_test = splits
    shap_plots = plot_shap_analysis(trained_models, X_train, X_test, get_feature_columns())
    
    # Generate PDF report
    generate_pdf_report(ml_results, backtest_results, importance_dict, df, shap_plots)
    
    # Save results
    results_df = pd.DataFrame({
        'strategy': list(backtest_results.keys()),
        'total_return': [r['total_return'] for r in backtest_results.values()],
        'sharpe_ratio': [r['sharpe_ratio'] for r in backtest_results.values()],
        'max_drawdown': [r['max_drawdown'] for r in backtest_results.values()],
        'win_rate': [r['win_rate'] for r in backtest_results.values()]
    })
    results_df.to_csv(os.path.join(OUTPUT_DIR, 'ml_backtest_results.csv'), index=False)
    
    print(f"\n✅ Analysis complete! Results saved to: {OUTPUT_DIR}")
    
    return df, ml_results, backtest_results


if __name__ == "__main__":
    df, ml_results, backtest_results = main()
