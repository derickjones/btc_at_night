#!/usr/bin/env python3
"""
GitHub Actions adapter for IBIT trading strategy.
Runs a single trading cycle instead of continuous loop.
"""

import sys
from datetime import datetime, time
import logging
from pathlib import Path

# Import your existing strategy
from strategy import IBITOvernightStrategy

def setup_logging():
    """Setup logging for GitHub Actions."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def should_buy_now():
    """Check if we should execute buy signal now."""
    now = datetime.now()
    # Check if it's a weekday and around 3:50 PM EST
    if now.weekday() < 5:  # Monday = 0, Friday = 4
        current_time = now.time()
        buy_time = time(15, 50)  # 3:50 PM
        # Allow 30 minute window around buy time
        return abs((datetime.combine(now.date(), current_time) - 
                   datetime.combine(now.date(), buy_time)).total_seconds()) < 1800
    return False

def should_sell_now():
    """Check if we should execute sell signal now."""
    now = datetime.now()
    # Check if it's a weekday and around 9:40 AM EST  
    if now.weekday() < 5:  # Monday = 0, Friday = 4
        current_time = now.time()
        sell_time = time(9, 40)  # 9:40 AM
        # Allow 30 minute window around sell time
        return abs((datetime.combine(now.date(), current_time) - 
                   datetime.combine(now.date(), sell_time)).total_seconds()) < 1800
    return False

def main():
    """Main GitHub Actions trading execution."""
    setup_logging()
    
    print(f"🚀 GitHub Actions IBIT Strategy - {datetime.now()}")
    
    try:
        # Initialize strategy
        strategy = IBITOvernightStrategy()
        
        # Check what action to take based on time
        if should_buy_now():
            print("🛒 Executing BUY signal...")
            strategy.execute_buy_signal()
        elif should_sell_now():
            print("🔄 Executing SELL signal...")
            strategy.execute_sell_signal()
        else:
            print("⏰ No trading action scheduled for current time")
            print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Always update performance metrics
            strategy._update_performance_metrics()
        
        print("✅ Trading cycle completed successfully")
        
    except Exception as e:
        print(f"❌ Error in trading cycle: {e}")
        logging.error(f"Trading error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()