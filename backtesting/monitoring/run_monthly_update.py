#!/usr/bin/env python3
"""
Quick Monthly Update Script
A simple script to run your monthly IBIT strategy update.
"""

import subprocess
import sys
from datetime import datetime

def run_monthly_update():
    """Run the monthly update with default settings."""
    
    print("🚀 IBIT Strategy Monthly Update")
    print("=" * 50)
    print(f"📅 Date: {datetime.now().strftime('%B %d, %Y')}")
    print()
    
    try:
        # Run the monthly update script
        print("Starting monthly update...")
        result = subprocess.run([
            sys.executable, 'monthly_update.py', 
            '--generate-pdf'
        ], check=True)
        
        print("\n✅ Monthly update completed successfully!")
        print("📄 Check results/IBIT_Strategy_Complete_Analysis.pdf for updated report")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Monthly update failed with error code: {e.returncode}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_monthly_update()