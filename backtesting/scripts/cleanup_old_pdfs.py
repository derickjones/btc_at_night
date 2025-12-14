#!/usr/bin/env python3
"""
PDF Cleanup Script
Removes old and duplicate PDF files, keeping only the most recent versions.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def cleanup_old_pdfs():
    """Remove old PDF files while keeping current ones."""
    
    print("🗂️  PDF CLEANUP")
    print("=" * 50)
    print(f"📅 Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
    
    results_dir = Path('results')
    total_size_freed = 0
    files_removed = 0
    
    # Files to clean up (older/duplicate versions)
    old_pdfs_to_remove = [
        'results/IBIT_Strategy_Analysis_Report.pdf',  # Superseded by complete analysis
        'results/IBIT_Strategy_Rolling_Analysis.pdf',  # Now included in complete analysis
    ]
    
    print("🗑️  REMOVING OLD PDF FILES:")
    print("-" * 35)
    
    for pdf_path in old_pdfs_to_remove:
        file_path = Path(pdf_path)
        if file_path.exists():
            # Get file size before deletion
            file_size = file_path.stat().st_size
            
            # Remove the file
            file_path.unlink()
            
            total_size_freed += file_size
            files_removed += 1
            
            # Convert size to readable format
            if file_size >= 1_000_000:
                size_str = f"{file_size / 1_000_000:.1f} MB"
            elif file_size >= 1_000:
                size_str = f"{file_size / 1_000:.1f} KB"
            else:
                size_str = f"{file_size} bytes"
            
            print(f"  ❌ Removed: {file_path.name} ({size_str})")
        else:
            print(f"  ⚠️  Not found: {file_path.name}")
    
    # Current files to keep
    print(f"\n📁 CURRENT PDF FILES TO KEEP:")
    print("-" * 35)
    
    current_pdfs = [
        'results/IBIT_Strategy_Complete_Analysis.pdf'  # Most current comprehensive report
    ]
    
    for pdf_path in current_pdfs:
        file_path = Path(pdf_path)
        if file_path.exists():
            file_size = file_path.stat().st_size
            
            if file_size >= 1_000_000:
                size_str = f"{file_size / 1_000_000:.1f} MB"
            elif file_size >= 1_000:
                size_str = f"{file_size / 1_000:.1f} KB"
            else:
                size_str = f"{file_size} bytes"
                
            print(f"  ✅ Keeping: {file_path.name} ({size_str})")
        else:
            print(f"  ❌ Missing: {file_path.name}")
    
    # Check backup files
    backup_dir = results_dir / 'backups'
    if backup_dir.exists():
        backup_pdfs = list(backup_dir.glob('**/*.pdf'))
        if backup_pdfs:
            print(f"\n📦 BACKUP PDF FILES:")
            print("-" * 35)
            for backup_pdf in backup_pdfs:
                file_size = backup_pdf.stat().st_size
                if file_size >= 1_000_000:
                    size_str = f"{file_size / 1_000_000:.1f} MB"
                else:
                    size_str = f"{file_size / 1_000:.1f} KB"
                
                backup_folder = backup_pdf.parent.name
                print(f"  📁 Backup: {backup_pdf.name} in {backup_folder} ({size_str})")
    
    # Summary
    print(f"\n📊 CLEANUP SUMMARY:")
    print("-" * 25)
    print(f"  🗑️  Files removed: {files_removed}")
    
    if total_size_freed >= 1_000_000:
        size_freed_str = f"{total_size_freed / 1_000_000:.1f} MB"
    elif total_size_freed >= 1_000:
        size_freed_str = f"{total_size_freed / 1_000:.1f} KB"
    else:
        size_freed_str = f"{total_size_freed} bytes"
    
    print(f"  💾 Space freed: {size_freed_str}")
    
    if files_removed > 0:
        print(f"\n✅ PDF CLEANUP COMPLETED!")
        print("📁 Current analysis available in: IBIT_Strategy_Complete_Analysis.pdf")
        print("📦 Previous versions safely backed up in results/backups/")
    else:
        print(f"\n✅ NO OLD PDFs TO REMOVE!")
        print("📁 All PDF files are current")
    
    return files_removed

if __name__ == "__main__":
    cleanup_old_pdfs()