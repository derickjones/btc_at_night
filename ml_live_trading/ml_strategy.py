"""
ML-Enhanced IBIT Overnight Trading Strategy
Uses trained ML model with intraday features to decide whether to buy.
"""

import json
import logging
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Tuple

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

from alpaca_client import AlpacaTradingClient
from config import (
    POSITION_SIZE_PCT, MIN_POSITION_SIZE, MAX_POSITION_SIZE,
    MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE,
    MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE, 
    RESULTS_DIR, SYMBOL, MODELS_DIR, LOGS_DIR,
    ML_BUY_THRESHOLD, ML_MODEL_TYPE
)


class MLOvernightStrategy:
    """ML-enhanced implementation of the IBIT overnight trading strategy."""
    
    def __init__(self):
        """Initialize the strategy."""
        self.client = AlpacaTradingClient()
        self.logger = self._setup_logging()
        self.trades_file = RESULTS_DIR / 'ml_live_trades.json'
        self.performance_file = RESULTS_DIR / 'ml_live_performance.json'
        self.predictions_file = RESULTS_DIR / 'ml_predictions.json'
        
        # Strategy state
        self.is_active = True
        self.model = None
        self.scaler = None
        
        # Load or train model
        self._load_or_train_model()
        
        # Load existing trade history
        self.trade_history = self._load_trade_history()
        self.prediction_history = self._load_prediction_history()
        
        self.logger.info("🚀 ML Overnight Strategy initialized")
        self.logger.info(f"   Model type: {ML_MODEL_TYPE}")
        self.logger.info(f"   Buy threshold: {ML_BUY_THRESHOLD}")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up strategy-specific logging."""
        logger = logging.getLogger('MLStrategy')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            log_file = LOGS_DIR / f'ml_strategy_{datetime.now().strftime("%Y%m%d")}.log'
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def _load_trade_history(self) -> list:
        """Load existing trade history from file."""
        if self.trades_file.exists():
            with open(self.trades_file, 'r') as f:
                return json.load(f)
        return []
    
    def _load_prediction_history(self) -> list:
        """Load prediction history from file."""
        if self.predictions_file.exists():
            with open(self.predictions_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_trade(self, trade_data: dict):
        """Save trade to history file."""
        self.trade_history.append(trade_data)
        with open(self.trades_file, 'w') as f:
            json.dump(self.trade_history, f, indent=2, default=str)
    
    def _save_prediction(self, prediction_data: dict):
        """Save prediction to history file."""
        self.prediction_history.append(prediction_data)
        with open(self.predictions_file, 'w') as f:
            json.dump(self.prediction_history, f, indent=2, default=str)
    
    def _load_or_train_model(self):
        """Load existing model or train a new one."""
        model_path = MODELS_DIR / f'{ML_MODEL_TYPE}_model.pkl'
        scaler_path = MODELS_DIR / f'{ML_MODEL_TYPE}_scaler.pkl'
        
        if model_path.exists() and scaler_path.exists():
            self.logger.info(f"Loading saved model from {model_path}")
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
        else:
            self.logger.info("Training new model...")
            self._train_model()
            
            # Save model
            with open(model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            self.logger.info(f"Model saved to {model_path}")
    
    def _train_model(self):
        """Train the ML model on historical data."""
        import yfinance as yf
        
        self.logger.info("Fetching historical data for training...")
        
        # Fetch historical data
        start_date = "2024-01-11"
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        ibit = yf.Ticker("IBIT")
        spy = yf.Ticker("SPY")
        
        ibit_df = ibit.history(start=start_date, end=end_date)
        spy_df = spy.history(start=start_date, end=end_date)
        
        # Create features
        df = self._create_training_features(ibit_df, spy_df)
        
        # Get feature columns and train
        feature_cols = self._get_feature_columns()
        X = df[feature_cols]
        y = df['target']
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model based on type
        if ML_MODEL_TYPE == 'logistic_regression':
            self.model = LogisticRegression(random_state=42, max_iter=1000)
        elif ML_MODEL_TYPE == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100, max_depth=5, min_samples_leaf=10, random_state=42
            )
        elif ML_MODEL_TYPE == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100, max_depth=3, min_samples_leaf=10, random_state=42
            )
        else:
            # Default to logistic regression
            self.model = LogisticRegression(random_state=42, max_iter=1000)
        
        # Fit model
        if ML_MODEL_TYPE == 'logistic_regression':
            self.model.fit(X_scaled, y)
        else:
            self.model.fit(X, y)
        
        self.logger.info(f"Model trained on {len(df)} samples")
    
    def _create_training_features(self, ibit_df: pd.DataFrame, spy_df: pd.DataFrame) -> pd.DataFrame:
        """Create feature matrix for training (matches ml_strategy_intraday.py)."""
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
        
        # Target: overnight return
        df['overnight_return'] = (df['ibit_open'].shift(-1) - df['ibit_close']) / df['ibit_close']
        
        # Create all features (same as ml_strategy_intraday.py)
        df = self._add_all_features(df)
        
        # Target variable
        df['target'] = (df['overnight_return'] > 0).astype(int)
        
        # Drop NaN rows
        df = df.dropna()
        
        return df
    
    def _add_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all features to dataframe."""
        # Datetime features
        df['day_of_week'] = df.index.dayofweek
        df['month'] = df.index.month
        df['day_of_month'] = df.index.day
        df['week_of_year'] = df.index.isocalendar().week.astype(int)
        df['quarter'] = df.index.quarter
        
        df['is_monday'] = (df['day_of_week'] == 0).astype(int)
        df['is_friday'] = (df['day_of_week'] == 4).astype(int)
        df['is_month_start'] = (df['day_of_month'] <= 5).astype(int)
        df['is_month_end'] = (df['day_of_month'] >= 25).astype(int)
        
        # Same-day intraday features
        df['today_gap'] = (df['ibit_open'] - df['ibit_close'].shift(1)) / df['ibit_close'].shift(1)
        df['spy_today_gap'] = (df['spy_open'] - df['spy_close'].shift(1)) / df['spy_close'].shift(1)
        df['gap_vs_spy'] = df['today_gap'] - df['spy_today_gap']
        
        df['intraday_return'] = (df['ibit_close'] - df['ibit_open']) / df['ibit_open']
        df['spy_intraday_return'] = (df['spy_close'] - df['spy_open']) / df['spy_open']
        df['intraday_vs_spy'] = df['intraday_return'] - df['spy_intraday_return']
        
        df['intraday_range'] = (df['ibit_high'] - df['ibit_low']) / df['ibit_open']
        df['spy_intraday_range'] = (df['spy_high'] - df['spy_low']) / df['spy_open']
        
        df['intraday_position'] = (df['ibit_close'] - df['ibit_low']) / (df['ibit_high'] - df['ibit_low'])
        df['intraday_position'] = df['intraday_position'].fillna(0.5)
        
        df['today_volume_scaled'] = df['ibit_volume'] * 0.9
        df['spy_today_volume_scaled'] = df['spy_volume'] * 0.9
        
        df['today_volume_vs_ma5'] = df['today_volume_scaled'] / df['ibit_volume'].shift(1).rolling(5).mean()
        df['today_volume_vs_ma20'] = df['today_volume_scaled'] / df['ibit_volume'].shift(1).rolling(20).mean()
        
        df['today_ibit_spy_vol_ratio'] = df['today_volume_scaled'] / df['spy_today_volume_scaled']
        
        # Previous overnight returns
        df['prev_overnight_1'] = df['overnight_return'].shift(1)
        df['prev_overnight_2'] = df['overnight_return'].shift(2)
        df['prev_overnight_3'] = df['overnight_return'].shift(3)
        df['prev_overnight_5_avg'] = df['overnight_return'].shift(1).rolling(5).mean()
        df['prev_overnight_5_std'] = df['overnight_return'].shift(1).rolling(5).std()
        df['prev_overnight_10_avg'] = df['overnight_return'].shift(1).rolling(10).mean()
        
        # Prior day returns
        df['prior_day_return'] = df['ibit_close'].shift(1).pct_change(1)
        df['prior_5d_return'] = df['ibit_close'].shift(1).pct_change(5)
        df['prior_10d_return'] = df['ibit_close'].shift(1).pct_change(10)
        df['prior_20d_return'] = df['ibit_close'].shift(1).pct_change(20)
        
        df['spy_prior_day_return'] = df['spy_close'].shift(1).pct_change(1)
        df['spy_prior_5d_return'] = df['spy_close'].shift(1).pct_change(5)
        
        df['ibit_vs_spy_prior_1d'] = df['prior_day_return'] - df['spy_prior_day_return']
        df['ibit_vs_spy_prior_5d'] = df['prior_5d_return'] - df['spy_prior_5d_return']
        
        # Prior volatility
        prior_returns = df['ibit_close'].shift(1).pct_change()
        df['prior_volatility_5d'] = prior_returns.rolling(5).std()
        df['prior_volatility_10d'] = prior_returns.rolling(10).std()
        df['prior_volatility_20d'] = prior_returns.rolling(20).std()
        
        # Price level features
        df['prior_close'] = df['ibit_close'].shift(1)
        df['prior_close_ma5'] = df['ibit_close'].shift(1).rolling(5).mean()
        df['prior_close_ma20'] = df['ibit_close'].shift(1).rolling(20).mean()
        df['prior_close_vs_ma5'] = df['prior_close'] / df['prior_close_ma5'] - 1
        df['prior_close_vs_ma20'] = df['prior_close'] / df['prior_close_ma20'] - 1
        
        df['current_vs_ma5'] = df['ibit_close'] / df['prior_close_ma5'] - 1
        df['current_vs_ma20'] = df['ibit_close'] / df['prior_close_ma20'] - 1
        
        return df
    
    def _get_feature_columns(self) -> list:
        """Return list of features used by the model."""
        return [
            # Datetime features
            'day_of_week', 'month', 'day_of_month', 'week_of_year', 'quarter',
            'is_monday', 'is_friday', 'is_month_start', 'is_month_end',
            
            # Same-day intraday features
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
    
    def calculate_features_live(self) -> Optional[pd.DataFrame]:
        """
        Calculate features using live data at 3:50 PM.
        Returns a DataFrame with one row containing all features.
        """
        self.logger.info("📊 Calculating live features...")
        
        try:
            import yfinance as yf
            
            # Get historical data for context (last 30 days)
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
            
            ibit = yf.Ticker("IBIT")
            spy = yf.Ticker("SPY")
            
            ibit_hist = ibit.history(start=start_date, end=end_date)
            spy_hist = spy.history(start=start_date, end=end_date)
            
            if ibit_hist.empty or spy_hist.empty:
                self.logger.error("Could not fetch historical data")
                return None
            
            # Get today's intraday data from Alpaca
            todays_ibit = self.client.get_todays_bar('IBIT')
            todays_spy = self.client.get_todays_bar('SPY')
            
            if not todays_ibit or not todays_spy:
                self.logger.warning("Could not get today's intraday data, using latest historical")
                # Use latest historical as fallback
                todays_ibit = {
                    'open': float(ibit_hist['Open'].iloc[-1]),
                    'high': float(ibit_hist['High'].iloc[-1]),
                    'low': float(ibit_hist['Low'].iloc[-1]),
                    'close': float(ibit_hist['Close'].iloc[-1]),
                    'volume': float(ibit_hist['Volume'].iloc[-1])
                }
                todays_spy = {
                    'open': float(spy_hist['Open'].iloc[-1]),
                    'high': float(spy_hist['High'].iloc[-1]),
                    'low': float(spy_hist['Low'].iloc[-1]),
                    'close': float(spy_hist['Close'].iloc[-1]),
                    'volume': float(spy_hist['Volume'].iloc[-1])
                }
            
            # Create feature row
            # Rename historical columns
            ibit_hist = ibit_hist.rename(columns={
                'Open': 'ibit_open', 'High': 'ibit_high', 'Low': 'ibit_low',
                'Close': 'ibit_close', 'Volume': 'ibit_volume'
            })
            
            spy_aligned = spy_hist.reindex(ibit_hist.index)
            ibit_hist['spy_open'] = spy_aligned['Open']
            ibit_hist['spy_high'] = spy_aligned['High']
            ibit_hist['spy_low'] = spy_aligned['Low']
            ibit_hist['spy_close'] = spy_aligned['Close']
            ibit_hist['spy_volume'] = spy_aligned['Volume']
            
            # Calculate overnight returns for historical data
            ibit_hist['overnight_return'] = (ibit_hist['ibit_open'].shift(-1) - ibit_hist['ibit_close']) / ibit_hist['ibit_close']
            
            # Get yesterday's data
            yesterday = ibit_hist.iloc[-1]
            
            # Build feature dictionary for today
            now = datetime.now()
            
            features = {
                # Datetime features
                'day_of_week': now.weekday(),
                'month': now.month,
                'day_of_month': now.day,
                'week_of_year': now.isocalendar()[1],
                'quarter': (now.month - 1) // 3 + 1,
                'is_monday': 1 if now.weekday() == 0 else 0,
                'is_friday': 1 if now.weekday() == 4 else 0,
                'is_month_start': 1 if now.day <= 5 else 0,
                'is_month_end': 1 if now.day >= 25 else 0,
                
                # Same-day intraday features
                'today_gap': (todays_ibit['open'] - yesterday['ibit_close']) / yesterday['ibit_close'],
                'spy_today_gap': (todays_spy['open'] - yesterday['spy_close']) / yesterday['spy_close'],
                'intraday_return': (todays_ibit['close'] - todays_ibit['open']) / todays_ibit['open'],
                'spy_intraday_return': (todays_spy['close'] - todays_spy['open']) / todays_spy['open'],
                'intraday_range': (todays_ibit['high'] - todays_ibit['low']) / todays_ibit['open'],
                'spy_intraday_range': (todays_spy['high'] - todays_spy['low']) / todays_spy['open'],
            }
            
            features['gap_vs_spy'] = features['today_gap'] - features['spy_today_gap']
            features['intraday_vs_spy'] = features['intraday_return'] - features['spy_intraday_return']
            
            # Intraday position (where in today's range is current price)
            intraday_range = todays_ibit['high'] - todays_ibit['low']
            if intraday_range > 0:
                features['intraday_position'] = (todays_ibit['close'] - todays_ibit['low']) / intraday_range
            else:
                features['intraday_position'] = 0.5
            
            # Volume features
            avg_vol_5 = ibit_hist['ibit_volume'].iloc[-5:].mean()
            avg_vol_20 = ibit_hist['ibit_volume'].iloc[-20:].mean()
            features['today_volume_vs_ma5'] = (todays_ibit['volume'] * 0.9) / avg_vol_5 if avg_vol_5 > 0 else 1.0
            features['today_volume_vs_ma20'] = (todays_ibit['volume'] * 0.9) / avg_vol_20 if avg_vol_20 > 0 else 1.0
            
            spy_avg_vol = spy_hist['Volume'].iloc[-5:].mean()
            features['today_ibit_spy_vol_ratio'] = (todays_ibit['volume'] * 0.9) / (todays_spy['volume'] * 0.9) if todays_spy['volume'] > 0 else 1.0
            
            # Previous overnight returns (from historical data)
            overnight_returns = ibit_hist['overnight_return'].dropna()
            features['prev_overnight_1'] = overnight_returns.iloc[-1] if len(overnight_returns) >= 1 else 0
            features['prev_overnight_2'] = overnight_returns.iloc[-2] if len(overnight_returns) >= 2 else 0
            features['prev_overnight_3'] = overnight_returns.iloc[-3] if len(overnight_returns) >= 3 else 0
            features['prev_overnight_5_avg'] = overnight_returns.iloc[-5:].mean() if len(overnight_returns) >= 5 else 0
            features['prev_overnight_5_std'] = overnight_returns.iloc[-5:].std() if len(overnight_returns) >= 5 else 0
            features['prev_overnight_10_avg'] = overnight_returns.iloc[-10:].mean() if len(overnight_returns) >= 10 else 0
            
            # Prior day returns
            features['prior_day_return'] = (yesterday['ibit_close'] - ibit_hist['ibit_close'].iloc[-2]) / ibit_hist['ibit_close'].iloc[-2]
            features['prior_5d_return'] = (yesterday['ibit_close'] - ibit_hist['ibit_close'].iloc[-6]) / ibit_hist['ibit_close'].iloc[-6]
            features['prior_10d_return'] = (yesterday['ibit_close'] - ibit_hist['ibit_close'].iloc[-11]) / ibit_hist['ibit_close'].iloc[-11]
            features['prior_20d_return'] = (yesterday['ibit_close'] - ibit_hist['ibit_close'].iloc[-21]) / ibit_hist['ibit_close'].iloc[-21]
            
            features['spy_prior_day_return'] = (yesterday['spy_close'] - ibit_hist['spy_close'].iloc[-2]) / ibit_hist['spy_close'].iloc[-2]
            features['spy_prior_5d_return'] = (yesterday['spy_close'] - ibit_hist['spy_close'].iloc[-6]) / ibit_hist['spy_close'].iloc[-6]
            
            features['ibit_vs_spy_prior_1d'] = features['prior_day_return'] - features['spy_prior_day_return']
            features['ibit_vs_spy_prior_5d'] = features['prior_5d_return'] - features['spy_prior_5d_return']
            
            # Prior volatility
            prior_returns = ibit_hist['ibit_close'].pct_change()
            features['prior_volatility_5d'] = prior_returns.iloc[-5:].std()
            features['prior_volatility_10d'] = prior_returns.iloc[-10:].std()
            features['prior_volatility_20d'] = prior_returns.iloc[-20:].std()
            
            # Price level features
            ma5 = ibit_hist['ibit_close'].iloc[-5:].mean()
            ma20 = ibit_hist['ibit_close'].iloc[-20:].mean()
            features['prior_close_vs_ma5'] = yesterday['ibit_close'] / ma5 - 1
            features['prior_close_vs_ma20'] = yesterday['ibit_close'] / ma20 - 1
            features['current_vs_ma5'] = todays_ibit['close'] / ma5 - 1
            features['current_vs_ma20'] = todays_ibit['close'] / ma20 - 1
            
            # Create DataFrame
            feature_cols = self._get_feature_columns()
            feature_row = pd.DataFrame([features])[feature_cols]
            
            self.logger.info(f"   Today's gap: {features['today_gap']:.2%}")
            self.logger.info(f"   Intraday return: {features['intraday_return']:.2%}")
            self.logger.info(f"   IBIT vs SPY (intraday): {features['intraday_vs_spy']:.2%}")
            
            return feature_row
            
        except Exception as e:
            self.logger.error(f"Error calculating features: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def get_ml_prediction(self) -> Tuple[bool, float]:
        """
        Get ML model prediction for tonight's overnight return.
        
        Returns:
            Tuple of (should_buy: bool, probability: float)
        """
        features = self.calculate_features_live()
        
        if features is None:
            self.logger.warning("Could not calculate features, defaulting to no buy")
            return False, 0.0
        
        try:
            # Scale features for logistic regression
            if ML_MODEL_TYPE == 'logistic_regression':
                features_scaled = self.scaler.transform(features)
                probability = self.model.predict_proba(features_scaled)[0, 1]
            else:
                probability = self.model.predict_proba(features)[0, 1]
            
            should_buy = probability >= ML_BUY_THRESHOLD
            
            self.logger.info(f"🤖 ML Prediction:")
            self.logger.info(f"   Probability of positive overnight: {probability:.1%}")
            self.logger.info(f"   Buy threshold: {ML_BUY_THRESHOLD:.1%}")
            self.logger.info(f"   Decision: {'BUY ✅' if should_buy else 'SKIP ❌'}")
            
            # Save prediction
            prediction_data = {
                'timestamp': datetime.now().isoformat(),
                'probability': float(probability),
                'threshold': ML_BUY_THRESHOLD,
                'decision': 'buy' if should_buy else 'skip',
                'features': features.iloc[0].to_dict()
            }
            self._save_prediction(prediction_data)
            
            return should_buy, probability
            
        except Exception as e:
            self.logger.error(f"Error getting prediction: {str(e)}")
            return False, 0.0
    
    def calculate_position_size(self) -> int:
        """Calculate position size based on available buying power."""
        try:
            account_info = self.client.get_account_info()
            buying_power = account_info.get('buying_power', 0)
            
            target_value = buying_power * POSITION_SIZE_PCT
            target_value = max(MIN_POSITION_SIZE, min(target_value, MAX_POSITION_SIZE))
            
            current_price = self.client.get_latest_price()
            if not current_price:
                self.logger.error("Could not get current price")
                return 0
            
            shares = int(target_value / current_price)
            
            self.logger.info(f"💰 Position size: {shares} shares "
                           f"(${target_value:.2f} / ${current_price:.2f} per share)")
            
            return shares
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {str(e)}")
            return 0
    
    def execute_buy_signal(self):
        """Execute buy order based on ML prediction."""
        if not self.is_active:
            self.logger.info("❌ Strategy inactive - skipping buy signal")
            return
        
        try:
            # Check if market is open
            if not self.client.is_market_open():
                self.logger.warning("Market is closed - cannot execute buy order")
                return
            
            # Check if we already have a position
            current_position = self.client.get_current_position()
            if current_position and current_position['qty'] > 0:
                self.logger.info(f"Already holding position: {current_position['qty']} shares")
                return
            
            # Get ML prediction
            should_buy, probability = self.get_ml_prediction()
            
            if not should_buy:
                self.logger.info(f"🤖 ML says SKIP tonight (prob={probability:.1%} < threshold={ML_BUY_THRESHOLD:.1%})")
                return
            
            # Calculate position size
            shares = self.calculate_position_size()
            if shares <= 0:
                self.logger.warning("Invalid position size - skipping trade")
                return
            
            # Get current price for logging
            current_price = self.client.get_latest_price()
            
            # Place buy order
            self.logger.info(f"🛒 Executing ML BUY signal (prob={probability:.1%})")
            self.logger.info(f"Target: {shares} shares at ~${current_price:.2f}")
            
            order_id = self.client.place_market_order('buy', shares)
            if not order_id:
                self.logger.error("Failed to place buy order")
                return
            
            # Wait for fill
            if self.client.wait_for_order_fill(order_id):
                # Record the trade
                trade_data = {
                    'timestamp': datetime.now().isoformat(),
                    'action': 'buy',
                    'shares': shares,
                    'price': current_price,
                    'order_id': order_id,
                    'ml_probability': probability,
                    'ml_threshold': ML_BUY_THRESHOLD
                }
                self._save_trade(trade_data)
                self.logger.info(f"✅ BUY order filled: {shares} shares")
            else:
                self.logger.error("Buy order not filled")
                
        except Exception as e:
            self.logger.error(f"Error executing buy signal: {str(e)}")
    
    def execute_sell_signal(self):
        """Execute sell order to close overnight position."""
        if not self.is_active:
            self.logger.info("❌ Strategy inactive - skipping sell signal")
            return
        
        try:
            # Check if market is open
            if not self.client.is_market_open():
                self.logger.warning("Market is closed - cannot execute sell order")
                return
            
            # Check if we have a position to sell
            current_position = self.client.get_current_position()
            if not current_position or current_position['qty'] <= 0:
                self.logger.info("No position to sell")
                return
            
            shares = int(current_position['qty'])
            entry_price = current_position['avg_entry_price']
            current_price = self.client.get_latest_price()
            
            # Place sell order
            self.logger.info(f"🔄 Executing SELL signal")
            self.logger.info(f"Selling {shares} shares at ~${current_price:.2f}")
            
            order_id = self.client.place_market_order('sell', shares)
            if not order_id:
                self.logger.error("Failed to place sell order")
                return
            
            # Wait for fill
            if self.client.wait_for_order_fill(order_id):
                # Calculate PnL
                pnl = (current_price - entry_price) * shares
                pnl_pct = (current_price - entry_price) / entry_price
                
                # Record the trade
                trade_data = {
                    'timestamp': datetime.now().isoformat(),
                    'action': 'sell',
                    'shares': shares,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'order_id': order_id
                }
                self._save_trade(trade_data)
                
                self.logger.info(f"✅ SELL order filled: {shares} shares")
                self.logger.info(f"   Entry: ${entry_price:.2f} -> Exit: ${current_price:.2f}")
                self.logger.info(f"   PnL: ${pnl:.2f} ({pnl_pct:.2%})")
            else:
                self.logger.error("Sell order not filled")
                
        except Exception as e:
            self.logger.error(f"Error executing sell signal: {str(e)}")
    
    def _update_performance_metrics(self):
        """Update and save performance metrics."""
        if not self.trade_history:
            return
        
        try:
            trades_df = pd.DataFrame(self.trade_history)
            
            # Filter to completed round trips (sell trades with pnl)
            sell_trades = trades_df[trades_df['action'] == 'sell']
            
            if 'pnl' in sell_trades.columns and len(sell_trades) > 0:
                total_pnl = sell_trades['pnl'].sum()
                winning_trades = (sell_trades['pnl'] > 0).sum()
                losing_trades = (sell_trades['pnl'] < 0).sum()
                win_rate = winning_trades / len(sell_trades) if len(sell_trades) > 0 else 0
                
                avg_win = sell_trades[sell_trades['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
                avg_loss = sell_trades[sell_trades['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
                
                # Count skipped predictions
                skipped = len([p for p in self.prediction_history if p.get('decision') == 'skip'])
                total_predictions = len(self.prediction_history)
                
                performance = {
                    'last_updated': datetime.now().isoformat(),
                    'total_trades': len(sell_trades),
                    'winning_trades': int(winning_trades),
                    'losing_trades': int(losing_trades),
                    'win_rate': float(win_rate),
                    'total_pnl': float(total_pnl),
                    'avg_win': float(avg_win),
                    'avg_loss': float(avg_loss),
                    'profit_factor': float(abs(avg_win / avg_loss)) if avg_loss != 0 else 0,
                    'total_predictions': total_predictions,
                    'skipped_nights': skipped,
                    'strategy_status': 'active' if self.is_active else 'stopped'
                }
                
                with open(self.performance_file, 'w') as f:
                    json.dump(performance, f, indent=2, default=str)
                
                self.logger.info(f"📊 Performance updated: {len(sell_trades)} trades, "
                               f"Win Rate: {win_rate:.1%}, Total PnL: ${total_pnl:.2f}")
                
        except Exception as e:
            self.logger.error(f"Error updating performance: {str(e)}")


if __name__ == "__main__":
    # Test the strategy
    strategy = MLOvernightStrategy()
    
    print("\n" + "="*60)
    print("Testing ML prediction...")
    print("="*60)
    
    should_buy, prob = strategy.get_ml_prediction()
    print(f"\nFinal decision: {'BUY' if should_buy else 'SKIP'} (probability: {prob:.1%})")
