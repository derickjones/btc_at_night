#!/usr/bin/env python3
"""
GitHub Actions adapter for IBIT trading strategy.
Runs a single trading cycle instead of continuous loop.
"""

import sys
from datetime import datetime, time, timezone, timedelta
import logging
from pathlib import Path

# Import your existing strategy
from strategy import IBITOvernightStrategy

# Eastern Time offset (EST = UTC-5, EDT = UTC-4)
# For simplicity, using EST. Adjust if needed for daylight saving.
EST_OFFSET = timedelta(hours=-5)

def get_est_now():
    """Get current time in Eastern Time."""
    utc_now = datetime.now(timezone.utc)
    est_now = utc_now + EST_OFFSET
    return est_now

def setup_logging():
    """Setup logging for GitHub Actions."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def should_buy_now():
    """Check if we should execute buy signal now."""
    now = get_est_now()
    # Check if it's a weekday and around 3:50 PM EST
    if now.weekday() < 5:  # Monday = 0, Friday = 4
        current_time = now.time()
        buy_time = time(15, 50)  # 3:50 PM EST
        # Allow 30 minute window around buy time
        return abs((datetime.combine(now.date(), current_time) - 
                   datetime.combine(now.date(), buy_time)).total_seconds()) < 1800
    return False

def should_sell_now():
    """Check if we should execute sell signal now."""
    now = get_est_now()
    # Check if it's a weekday and around 9:31 AM EST (just after market open)
    if now.weekday() < 5:  # Monday = 0, Friday = 4
        current_time = now.time()
        sell_time = time(9, 31)  # 9:31 AM EST - just after market open
        # Allow 30 minute window around sell time
        return abs((datetime.combine(now.date(), current_time) - 
                   datetime.combine(now.date(), sell_time)).total_seconds()) < 1800
    return False

def main():
    """Main GitHub Actions trading execution."""
    setup_logging()
    
    est_now = get_est_now()
    utc_now = datetime.now(timezone.utc)
    
    print(f"🚀 GitHub Actions IBIT Strategy")
    print(f"   UTC time: {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   EST time: {est_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
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
            print(f"   should_buy_now(): {should_buy_now()} (target: 15:50 EST)")
            print(f"   should_sell_now(): {should_sell_now()} (target: 09:40 EST)")
            
            # Always update performance metrics
            strategy._update_performance_metrics()
        
        print("✅ Trading cycle completed successfully")
        
    except Exception as e:
        print(f"❌ Error in trading cycle: {e}")
        logging.error(f"Trading error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()