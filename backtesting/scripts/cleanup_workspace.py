#!/usr/bin/env python3
"""
Workspace Cleanup Script
Removes orphaned and redundant files to keep the workspace clean.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def cleanup_workspace():
    """Clean up orphaned and redundant files."""
    
    print("🧹 WORKSPACE CLEANUP")
    print("=" * 50)
    print(f"📅 Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    print()
    
    # Create archive directory for important old files
    archive_dir = Path('archive')
    archive_dir.mkdir(exist_ok=True)
    
    # Files to delete completely (development/demo files)
    files_to_delete = [
        'chart_demo.py',           # Chart demonstration script
        'monitoring_demo.py',      # Monitoring demo script
        'debug_monitor.py',        # Debug script
        'extract_monitoring_results.py',  # Development utility
        'create_rolling_charts.py',      # Standalone chart creator (now integrated)
        'create_simple_pdf.py',   # Simple PDF generator (superseded)
        'analysis_summary.py',    # Old summary script (superseded)
        'create_summary.py'       # Old summary creator (superseded)
    ]
    
    # Files to archive (old but potentially valuable)
    files_to_archive = [
        'create_pdf_report.py',   # Old PDF generator (60KB - has complex logic)
        'generate_report.py',     # Old report generator
        'run_monthly_check.py',   # Old monthly check script
        'analyze_dual_strategy.py',      # Dual strategy analysis
        'analyze_ibit_strc_strategy.py'  # STRC analysis (failed strategy)
    ]
    
    deleted_size = 0
    archived_size = 0
    
    # Delete development files
    print("🗑️  DELETING DEVELOPMENT FILES:")
    print("-" * 35)
    for file in files_to_delete:
        if os.path.exists(file):
            size = os.path.getsize(file)
            os.remove(file)
            deleted_size += size
            print(f"  ❌ Deleted: {file} ({size:,} bytes)")
        else:
            print(f"  ⚪ Not found: {file}")
    
    print()
    
    # Archive old files
    print("📦 ARCHIVING OLD FILES:")
    print("-" * 25)
    for file in files_to_archive:
        if os.path.exists(file):
            size = os.path.getsize(file)
            archive_path = archive_dir / file
            shutil.move(file, archive_path)
            archived_size += size
            print(f"  📁 Archived: {file} → archive/{file} ({size:,} bytes)")
        else:
            print(f"  ⚪ Not found: {file}")
    
    print()
    
    # Clean up __pycache__ directories
    print("🧹 CLEANING CACHE FILES:")
    print("-" * 25)
    pycache_dirs = []
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                pycache_dirs.append(os.path.join(root, dir_name))
    
    cache_size = 0
    for pycache_dir in pycache_dirs:
        if os.path.exists(pycache_dir):
            # Calculate size before deletion
            for root, dirs, files in os.walk(pycache_dir):
                for file in files:
                    cache_size += os.path.getsize(os.path.join(root, file))
            shutil.rmtree(pycache_dir)
            print(f"  🗑️  Removed: {pycache_dir}")
    
    # Remove .DS_Store files
    ds_store_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file == '.DS_Store':
                ds_store_files.append(os.path.join(root, file))
    
    ds_store_size = 0
    for ds_store_file in ds_store_files:
        if os.path.exists(ds_store_file):
            ds_store_size += os.path.getsize(ds_store_file)
            os.remove(ds_store_file)
            print(f"  🗑️  Removed: {ds_store_file}")
    
    print()
    
    # Summary
    print("📊 CLEANUP SUMMARY:")
    print("-" * 20)
    print(f"  🗑️  Files deleted: {len([f for f in files_to_delete if not os.path.exists(f)])} files, {deleted_size:,} bytes ({deleted_size/1024:.1f} KB)")
    print(f"  📦 Files archived: {len([f for f in files_to_archive if os.path.exists(archive_dir/f)])} files, {archived_size:,} bytes ({archived_size/1024:.1f} KB)")
    print(f"  🧹 Cache cleaned: {cache_size:,} bytes ({cache_size/1024:.1f} KB)")
    print(f"  📁 .DS_Store removed: {ds_store_size:,} bytes")
    
    total_freed = deleted_size + cache_size + ds_store_size
    print(f"  💾 Total space freed: {total_freed:,} bytes ({total_freed/1024:.1f} KB)")
    
    print()
    print("✅ WORKSPACE CLEANED!")
    print("📁 Archived files are in ./archive/ if you need them later")
    print("🚀 Your workspace is now optimized for monthly updates")

if __name__ == "__main__":
    cleanup_workspace()