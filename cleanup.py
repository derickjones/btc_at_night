#!/usr/bin/env python3
"""
Cleanup script for IBIT trading project.
Removes temporary files, old logs, and keeps the repository clean.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import argparse

def clean_python_cache(project_root):
    """Remove Python cache files and directories."""
    removed = 0
    for root, dirs, files in os.walk(project_root):
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            cache_dir = Path(root) / '__pycache__'
            shutil.rmtree(cache_dir, ignore_errors=True)
            print(f"🗑️ Removed: {cache_dir}")
            removed += 1
        
        # Remove .pyc files
        for file in files:
            if file.endswith('.pyc'):
                pyc_file = Path(root) / file
                pyc_file.unlink(missing_ok=True)
                print(f"🗑️ Removed: {pyc_file}")
                removed += 1
    
    return removed

def clean_system_files(project_root):
    """Remove system-specific files (.DS_Store, Thumbs.db)."""
    removed = 0
    system_files = ['.DS_Store', 'Thumbs.db', 'Desktop.ini']
    
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file in system_files:
                system_file = Path(root) / file
                system_file.unlink(missing_ok=True)
                print(f"🗑️ Removed: {system_file}")
                removed += 1
    
    return removed

def clean_old_logs(logs_dir, days=30):
    """Remove log files older than specified days."""
    if not logs_dir.exists():
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=days)
    removed = 0
    
    for log_file in logs_dir.glob('*.log'):
        if log_file.stat().st_mtime < cutoff_date.timestamp():
            log_file.unlink(missing_ok=True)
            print(f"🗑️ Removed old log: {log_file}")
            removed += 1
    
    return removed

def clean_temp_files(project_root):
    """Remove temporary files."""
    removed = 0
    temp_patterns = ['*.tmp', '*.temp', '*.swp', '*.swo']
    
    for pattern in temp_patterns:
        for temp_file in Path(project_root).rglob(pattern):
            if temp_file.is_file():
                temp_file.unlink(missing_ok=True)
                print(f"🗑️ Removed temp file: {temp_file}")
                removed += 1
    
    return removed

def main():
    """Main cleanup function."""
    parser = argparse.ArgumentParser(description='Clean up IBIT trading project')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be cleaned without actually doing it')
    parser.add_argument('--logs-days', type=int, default=30,
                       help='Keep logs newer than this many days (default: 30)')
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent
    
    print(f"🧹 Cleaning up project: {project_root}")
    print(f"Dry run: {args.dry_run}")
    print("=" * 50)
    
    if args.dry_run:
        print("DRY RUN - No files will actually be removed")
        return
    
    # Clean different types of files
    python_removed = clean_python_cache(project_root)
    system_removed = clean_system_files(project_root)
    temp_removed = clean_temp_files(project_root)
    
    # Clean old logs in both locations
    backtesting_logs = project_root / 'backtesting' / 'logs'
    live_logs = project_root / 'live_trading' / 'logs'
    
    logs_removed = 0
    logs_removed += clean_old_logs(backtesting_logs, args.logs_days)
    logs_removed += clean_old_logs(live_logs, args.logs_days)
    
    print("=" * 50)
    print(f"✅ Cleanup complete!")
    print(f"   Python cache files: {python_removed}")
    print(f"   System files: {system_removed}")
    print(f"   Temporary files: {temp_removed}")
    print(f"   Old log files: {logs_removed}")
    print(f"   Total removed: {python_removed + system_removed + temp_removed + logs_removed}")

if __name__ == "__main__":
    main()