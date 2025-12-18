"""
Setup and Testing Script for Alpaca Paper Trading
Validates configuration and tests connection before live trading.
"""

import os
import sys
from pathlib import Path
import json

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from alpaca_client import AlpacaTradingClient
from config import ALPACA_API_KEY, ALPACA_SECRET_KEY, SYMBOL, RESULTS_DIR


def check_dependencies():
    """Check if required packages are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'alpaca_trade_api',
        'schedule', 
        'pandas',
        'numpy',
        'matplotlib'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed")
    return True


def check_configuration():
    """Validate configuration settings."""
    print("\n🔧 Checking configuration...")
    
    # Check API credentials
    if ALPACA_API_KEY == 'your_paper_trading_api_key_here':
        print("❌ ALPACA_API_KEY not configured")
        print("   Update config.py with your Alpaca paper trading API key")
        return False
    
    if ALPACA_SECRET_KEY == 'your_paper_trading_secret_key_here':
        print("❌ ALPACA_SECRET_KEY not configured")
        print("   Update config.py with your Alpaca paper trading secret key")
        return False
    
    print(f"✅ API Key configured: {ALPACA_API_KEY[:8]}...")
    print(f"✅ Secret Key configured: {ALPACA_SECRET_KEY[:8]}...")
    
    # Check directories
    for directory in [RESULTS_DIR, RESULTS_DIR.parent / 'logs', RESULTS_DIR.parent / 'data']:
        if directory.exists():
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"⚠️ Creating directory: {directory}")
            directory.mkdir(parents=True, exist_ok=True)
    
    print("✅ Configuration validated")
    return True


def test_alpaca_connection():
    """Test connection to Alpaca API."""
    print("\n📡 Testing Alpaca connection...")
    
    try:
        client = AlpacaTradingClient()
        
        if not client.connect():
            print("❌ Failed to connect to Alpaca")
            return False
        
        # Test account access
        account_info = client.get_account_info()
        if not account_info:
            print("❌ Could not retrieve account information")
            return False
        
        print(f"✅ Account Status: Active")
        print(f"✅ Buying Power: ${account_info['buying_power']:,.2f}")
        print(f"✅ Portfolio Value: ${account_info['portfolio_value']:,.2f}")
        
        # Test market data access
        price = client.get_latest_price()
        if price:
            print(f"✅ {SYMBOL} Current Price: ${price:.2f}")
        else:
            print(f"⚠️ Could not fetch {SYMBOL} price")
        
        # Test market status
        market_open = client.is_market_open()
        print(f"✅ Market Status: {'Open' if market_open else 'Closed'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("1. Verify your API credentials in config.py")
        print("2. Ensure you're using paper trading credentials")
        print("3. Check your internet connection")
        return False


def create_sample_config():
    """Create a sample configuration file."""
    print("\n📝 Creating sample configuration...")
    
    sample_config = {
        "alpaca_setup": {
            "api_key": "your_paper_trading_api_key_here",
            "secret_key": "your_paper_trading_secret_key_here",
            "base_url": "https://paper-api.alpaca.markets",
            "note": "Get these from: https://app.alpaca.markets/paper/dashboard/overview"
        },
        "strategy_settings": {
            "symbol": "IBIT",
            "position_size_pct": 0.95,
            "max_position_size": 10000,
            "max_daily_loss": 0.05
        },
        "schedule": {
            "buy_time": "16:00",
            "sell_time": "09:30",
            "timezone": "US/Eastern"
        }
    }
    
    config_file = Path(__file__).parent / 'sample_config.json'
    with open(config_file, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"✅ Sample configuration saved: {config_file}")
    return str(config_file)


def run_validation_test():
    """Run a comprehensive validation test."""
    print("🚀 ALPACA PAPER TRADING SETUP VALIDATION")
    print("=" * 50)
    
    # Track validation results
    validations = {
        'dependencies': False,
        'configuration': False,
        'connection': False
    }
    
    # Run all checks
    validations['dependencies'] = check_dependencies()
    
    if validations['dependencies']:
        validations['configuration'] = check_configuration()
        
        if validations['configuration']:
            validations['connection'] = test_alpaca_connection()
    
    # Summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    for check, passed in validations.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{check.upper()}: {status}")
    
    all_passed = all(validations.values())
    
    if all_passed:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("Your Alpaca paper trading setup is ready!")
        print("\nNext steps:")
        print("1. Run: python strategy.py")
        print("2. Monitor with: python monitor.py")
    else:
        print("\n⚠️ SOME VALIDATIONS FAILED")
        print("Please fix the issues above before proceeding.")
        
        if not validations['configuration']:
            print("\n🔧 Configuration Help:")
            print("1. Sign up for Alpaca paper trading: https://alpaca.markets/")
            print("2. Get your API keys from: https://app.alpaca.markets/paper/dashboard/overview")
            print("3. Update config.py with your credentials")
    
    return all_passed


def main():
    """Main setup validation."""
    try:
        success = run_validation_test()
        
        if not success:
            create_sample_config()
            print(f"\n📋 Next steps:")
            print("1. Get Alpaca paper trading account")
            print("2. Update config.py with your API credentials") 
            print("3. Run this script again: python setup.py")
        
        return success
        
    except KeyboardInterrupt:
        print("\n⏹️ Setup cancelled by user")
        return False
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        return False


if __name__ == "__main__":
    main()