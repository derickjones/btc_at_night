#!/usr/bin/env python3
"""
Daily Email Report Sender for IBIT Trading Strategy
Automatically sends daily performance reports via email.

Usage:
    python daily_email_report.py

For scheduling (cron example):
    30 17 * * 1-5 cd /path/to/live_trading && python daily_email_report.py

This runs at 5:30 PM Monday-Friday (after market close)
"""

import sys
from pathlib import Path
from datetime import datetime
import logging

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from monitor import PerformanceMonitor
from config import ENABLE_DAILY_EMAIL_REPORTS, EMAIL_APP_PASSWORD

def setup_logging():
    """Setup logging for daily email reports."""
    log_file = Path(__file__).parent / 'logs' / f'daily_email_{datetime.now().strftime("%Y%m")}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def check_configuration():
    """Check if email configuration is properly set up."""
    if not ENABLE_DAILY_EMAIL_REPORTS:
        logging.warning("Daily email reports are disabled in config")
        return False
    
    if not EMAIL_APP_PASSWORD:
        logging.error("EMAIL_APP_PASSWORD not set in config.py")
        print("\n🔧 EMAIL SETUP REQUIRED:")
        print("1. Go to your Google Account settings")
        print("2. Enable 2-Factor Authentication")
        print("3. Generate an App Password for this application")
        print("4. Set EMAIL_APP_PASSWORD in config.py to your App Password")
        print("5. Make sure EMAIL_FROM matches your Gmail address")
        return False
    
    return True

def main():
    """Main function to send daily email report."""
    setup_logging()
    
    logging.info("Starting daily email report process")
    
    # Check configuration
    if not check_configuration():
        logging.error("Email configuration incomplete - exiting")
        sys.exit(1)
    
    try:
        # Initialize monitor
        monitor = PerformanceMonitor()
        
        # Generate and send report
        success = monitor.generate_and_send_daily_report()
        
        if success:
            logging.info("Daily email report sent successfully")
            print("✅ Daily email report sent!")
        else:
            logging.error("Failed to send daily email report")
            print("❌ Failed to send daily email report")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Unexpected error in daily email report: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()