#!/usr/bin/env python3
"""
Monthly Strategy Update System
Automatically updates IBIT strategy analysis with latest trading data.
Run this script monthly to keep your analysis current.

Usage: python monthly_update.py [--full-reanalysis] [--generate-pdf]
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path
import argparse
import subprocess
import json

# Add core directory to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core'))

from data_fetcher import IBITDataFetcher
from strategy import IBITOvernightStrategy
from backtester import BacktestEngine
import config

class MonthlyUpdater:
    """Handles monthly updates of IBIT strategy analysis."""
    
    def __init__(self):
        self.current_date = datetime.now()
        
        # Use paths relative to backtesting root directory
        backtesting_root = Path(__file__).parent.parent
        self.last_update_file = backtesting_root / 'results' / 'last_update.json'
        self.backup_dir = backtesting_root / 'results' / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the correct Python executable path
        self.python_exe = sys.executable
        
    def check_last_update(self):
        """Check when the analysis was last updated."""
        if self.last_update_file.exists():
            with open(self.last_update_file, 'r') as f:
                last_update_data = json.load(f)
                last_update = datetime.fromisoformat(last_update_data['date'])
                return last_update, last_update_data
        return None, None
    
    def backup_current_results(self):
        """Backup current results before updating."""
        print("📁 Creating backup of current results...")
        
        timestamp = self.current_date.strftime('%Y%m%d_%H%M%S')
        backup_folder = self.backup_dir / f'backup_{timestamp}'
        backup_folder.mkdir(exist_ok=True)
        
        # Get the backtesting root directory
        backtesting_root = Path(__file__).parent.parent
        
        # Files to backup with correct paths
        backup_files = [
            'results/trade_results.csv',
            'results/performance_summary.csv',
            'results/IBIT_Strategy_Complete_Analysis.pdf',
            'results/ibit_spy_performance.csv',
            'results/ibit_spy_combined_strategy.csv'
        ]
        
        for file_path in backup_files:
            full_path = backtesting_root / file_path
            if full_path.exists():
                filename = full_path.name
                backup_path = backup_folder / filename
                subprocess.run(['cp', str(full_path), str(backup_path)], check=False)
        
        print(f"✅ Backup created: {backup_folder}")
        return backup_folder
    
    def fetch_latest_data(self, start_date=None):
        """Fetch the latest IBIT data."""
        print("📊 Fetching latest IBIT data...")
        
        if start_date is None:
            # Default to fetching from beginning to ensure we have complete data
            start_date = "2024-01-10"
        
        # Extend end date to ensure we get the latest data
        end_date = (self.current_date + timedelta(days=1)).strftime('%Y-%m-%d')
        
        fetcher = IBITDataFetcher()
        
        try:
            # Fetch processed strategy data (not just raw OHLCV)
            data = fetcher.get_strategy_data(start_date, end_date, use_cache=False)
            
            if data is None or len(data) == 0:
                print("❌ No new data available")
                return None
                
            print(f"✅ Fetched {len(data)} days of data")
            print(f"📅 Data range: {data['trade_date'].iloc[0]} to {data['trade_date'].iloc[-1]}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return None
    
    def run_strategy_analysis(self, data):
        """Run the complete strategy analysis with new data."""
        print("🚀 Running strategy analysis...")
        
        try:
            # Initialize strategy and backtest engine
            strategy = IBITOvernightStrategy()
            backtest = BacktestEngine()
            
            # Run backtest
            results = backtest.run_backtest(data, strategy)
            
            if results is None:
                print("❌ Backtest failed")
                return False
            
            print(f"✅ Analysis complete: {len(results[0])} trades analyzed")
            return True
            
        except Exception as e:
            print(f"❌ Error running analysis: {e}")
            return False
    
    def run_spy_analysis(self):
        """Run the SPY enhancement analysis if requested."""
        print("📈 Running SPY enhancement analysis...")
        
        try:
            # Get the backtesting root and change to analysis directory
            backtesting_root = Path(__file__).parent.parent
            analysis_dir = backtesting_root / 'analysis'
            
            # Run the SPY analysis script from the analysis directory
            result = subprocess.run([self.python_exe, 'analyze_ibit_spy_strategy.py'], 
                                  capture_output=True, text=True, check=False, cwd=analysis_dir)
            
            if result.returncode == 0:
                print("✅ SPY analysis completed successfully")
                return True
            else:
                print(f"❌ SPY analysis failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error running SPY analysis: {e}")
            return False
    
    def generate_pdf_report(self):
        """Generate the updated comprehensive PDF report."""
        print("📄 Generating comprehensive PDF report...")
        
        try:
            # Get the backtesting root and change to analysis directory
            backtesting_root = Path(__file__).parent.parent
            analysis_dir = backtesting_root / 'analysis'
            
            # Run the combined PDF generator from the analysis directory
            result = subprocess.run([self.python_exe, 'create_combined_pdf.py'], 
                                  capture_output=True, text=True, check=False, cwd=analysis_dir)
            
            if result.returncode == 0:
                print("✅ PDF report generated successfully")
                return True
            else:
                print(f"❌ PDF generation failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error generating PDF: {e}")
            return False
    
    def run_monthly_monitoring(self):
        """Run the monthly monitoring analysis."""
        print("📊 Running monthly monitoring analysis...")
        
        try:
            # Run from the current monitoring directory
            result = subprocess.run([self.python_exe, 'monthly_monitor.py'], 
                                  capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                print("✅ Monthly monitoring completed")
                return True
            else:
                print(f"⚠️ Monthly monitoring had issues: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error running monthly monitoring: {e}")
            return False
    
    def update_last_update_record(self, notes=""):
        """Update the record of when analysis was last updated."""
        update_data = {
            'date': self.current_date.isoformat(),
            'notes': notes,
            'version': '1.0'
        }
        
        with open(self.last_update_file, 'w') as f:
            json.dump(update_data, f, indent=2)
    
    def print_summary(self, success_steps):
        """Print a summary of the update process."""
        print("\n" + "="*60)
        print("📋 MONTHLY UPDATE SUMMARY")
        print("="*60)
        
        total_steps = len(success_steps)
        successful_steps = sum(success_steps.values())
        
        print(f"📅 Update Date: {self.current_date.strftime('%B %d, %Y at %I:%M %p')}")
        print(f"✅ Successful Steps: {successful_steps}/{total_steps}")
        print()
        
        print("📊 Step Results:")
        for step, success in success_steps.items():
            status = "✅" if success else "❌"
            print(f"   {status} {step}")
        
        if successful_steps == total_steps:
            print(f"\n🎉 Monthly update completed successfully!")
            print(f"📄 Updated PDF: results/IBIT_Strategy_Complete_Analysis.pdf")
            print(f"📊 Monthly monitoring: results/monthly_monitoring/")
        else:
            print(f"\n⚠️  Monthly update completed with {total_steps - successful_steps} issues")
            print(f"💡 Check the error messages above for details")
        
        print("="*60)
    
    def run_full_update(self, args):
        """Run the complete monthly update process."""
        print("🚀 STARTING MONTHLY IBIT STRATEGY UPDATE")
        print("="*60)
        
        # Check last update
        last_update, last_data = self.check_last_update()
        if last_update:
            days_since = (self.current_date - last_update).days
            print(f"📅 Last update: {last_update.strftime('%B %d, %Y')} ({days_since} days ago)")
        else:
            print("📅 First time running monthly update")
        
        print(f"📅 Current update: {self.current_date.strftime('%B %d, %Y')}")
        print()
        
        # Track success of each step
        success_steps = {}
        
        # Step 1: Backup current results
        backup_path = self.backup_current_results()
        success_steps['Backup Current Results'] = backup_path is not None
        
        # Step 2: Fetch latest data
        if args.full_reanalysis:
            print("🔄 Full reanalysis requested - fetching all data")
            data = self.fetch_latest_data()
        else:
            # Fetch data from last month
            start_date = (self.current_date - timedelta(days=45)).strftime('%Y-%m-%d')
            data = self.fetch_latest_data(start_date)
        
        success_steps['Fetch Latest Data'] = data is not None
        
        # Step 3: Run strategy analysis
        if data is not None:
            analysis_success = self.run_strategy_analysis(data)
            success_steps['Run Strategy Analysis'] = analysis_success
        else:
            success_steps['Run Strategy Analysis'] = False
        
        # Step 4: Run SPY analysis
        spy_success = self.run_spy_analysis()
        success_steps['Run SPY Enhancement Analysis'] = spy_success
        
        # Step 5: Run monthly monitoring
        monitoring_success = self.run_monthly_monitoring()
        success_steps['Run Monthly Monitoring'] = monitoring_success
        
        # Step 6: Generate PDF report
        if args.generate_pdf:
            pdf_success = self.generate_pdf_report()
            success_steps['Generate PDF Report'] = pdf_success
        
        # Step 7: Update records
        self.update_last_update_record(f"Monthly update - {len(success_steps)} steps")
        success_steps['Update Records'] = True
        
        # Print summary
        self.print_summary(success_steps)
        
        return all(success_steps.values())

def main():
    """Main function to handle command line arguments and run update."""
    parser = argparse.ArgumentParser(description='Monthly IBIT Strategy Update')
    parser.add_argument('--full-reanalysis', action='store_true', 
                       help='Run complete reanalysis from beginning (slower but more thorough)')
    parser.add_argument('--generate-pdf', action='store_true', default=True,
                       help='Generate updated PDF report (default: True)')
    parser.add_argument('--quick', action='store_true',
                       help='Quick update - skip PDF generation')
    
    args = parser.parse_args()
    
    # Handle quick mode
    if args.quick:
        args.generate_pdf = False
    
    # Run the update
    updater = MonthlyUpdater()
    success = updater.run_full_update(args)
    
    if success:
        print("🎊 Monthly update completed successfully!")
        sys.exit(0)
    else:
        print("❌ Monthly update completed with errors")
        sys.exit(1)

if __name__ == "__main__":
    # Import json here to avoid import errors in main
    import json
    main()