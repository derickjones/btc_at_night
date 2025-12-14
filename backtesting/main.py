#!/usr/bin/env python3
"""
IBIT Backtesting Suite - Main Entry Point
=========================================

A comprehensive backtesting and monitoring system for IBIT overnight trading strategy.

Quick Start:
-----------
1. Run analysis:        python main.py analyze
2. Monthly update:      python main.py update  
3. Generate report:     python main.py report
4. Monitor performance: python main.py monitor

For more options:       python main.py --help
"""

import sys
import os
import subprocess
from pathlib import Path

# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent / 'core'))
sys.path.insert(0, str(Path(__file__).parent / 'analysis'))
sys.path.insert(0, str(Path(__file__).parent / 'monitoring'))

def main():
    """Main entry point for the backtesting suite."""
    
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    # Get the backtesting root directory
    backtesting_root = Path(__file__).parent.absolute()
    
    # Add all subdirectories to Python path for imports
    for subdir in ['core', 'analysis', 'monitoring']:
        subdir_path = str(backtesting_root / subdir)
        if subdir_path not in sys.path:
            sys.path.insert(0, subdir_path)
    
    if command == 'analyze':
        print("🚀 Running IBIT strategy analysis...")
        os.chdir(backtesting_root / 'analysis')
        exec(open('analyze.py').read())
        
    elif command == 'update':
        print("📊 Running monthly update...")
        os.chdir(backtesting_root / 'monitoring')
        exec(open('run_monthly_update.py').read())
        
    elif command == 'report':
        print("📄 Generating comprehensive PDF report...")
        os.chdir(backtesting_root / 'analysis')
        result = subprocess.run([sys.executable, 'create_combined_pdf.py'], 
                              capture_output=False, text=True)
        if result.returncode != 0:
            print(f"❌ PDF generation failed with code {result.returncode}")
        
    elif command == 'monitor':
        print("📈 Running performance monitoring...")
        os.chdir(backtesting_root / 'monitoring')
        exec(open('monthly_monitor.py').read())
        
    elif command in ['--help', '-h', 'help']:
        print(__doc__)
        
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: analyze, update, report, monitor")
        print("Use 'python main.py --help' for more information")

if __name__ == '__main__':
    main()
