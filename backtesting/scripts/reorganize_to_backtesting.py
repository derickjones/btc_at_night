#!/usr/bin/env python3
"""
Project Reorganization Script
Reorganizes the entire project into a clean 'backtesting' folder structure.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def create_backtesting_structure():
    """Create the new backtesting folder structure."""
    
    print("📁 BACKTESTING PROJECT REORGANIZATION")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
    
    # Define the new structure
    backtesting_root = Path('backtesting')
    
    # Create main backtesting directory
    backtesting_root.mkdir(exist_ok=True)
    
    # Define subdirectories
    subdirs = {
        'core': 'Core strategy implementation and backtesting engine',
        'analysis': 'Analysis scripts and strategy variations', 
        'monitoring': 'Monthly monitoring and automation',
        'data': 'Market data and cached files',
        'results': 'Analysis outputs, reports, and backups',
        'docs': 'Documentation and guides',
        'scripts': 'Utility and maintenance scripts'
    }
    
    # Create subdirectories
    print("🏗️  CREATING DIRECTORY STRUCTURE:")
    print("-" * 40)
    for subdir, description in subdirs.items():
        full_path = backtesting_root / subdir
        full_path.mkdir(exist_ok=True)
        print(f"  📁 {subdir}/ - {description}")
    
    return backtesting_root, subdirs

def reorganize_files():
    """Reorganize all files into the new structure."""
    
    backtesting_root, subdirs = create_backtesting_structure()
    
    # File mapping: source -> destination
    file_moves = [
        # Core strategy files
        ('src/strategy.py', 'backtesting/core/strategy.py'),
        ('src/backtester.py', 'backtesting/core/backtester.py'),
        ('src/data_fetcher.py', 'backtesting/core/data_fetcher.py'),
        ('src/visualization.py', 'backtesting/core/visualization.py'),
        ('config.py', 'backtesting/core/config.py'),
        
        # Analysis scripts
        ('analyze.py', 'backtesting/analysis/analyze.py'),
        ('analyze_ibit_spy_strategy.py', 'backtesting/analysis/analyze_ibit_spy_strategy.py'),
        ('src/strategy_comparison.py', 'backtesting/analysis/strategy_comparison.py'),
        ('create_combined_pdf.py', 'backtesting/analysis/create_combined_pdf.py'),
        
        # Monitoring system
        ('monthly_update.py', 'backtesting/monitoring/monthly_update.py'),
        ('run_monthly_update.py', 'backtesting/monitoring/run_monthly_update.py'),
        ('monthly_monitor.py', 'backtesting/monitoring/monthly_monitor.py'),
        ('historical_tracker.py', 'backtesting/monitoring/historical_tracker.py'),
        
        # Documentation
        ('README.md', 'backtesting/docs/README.md'),
        ('MONITORING_README.md', 'backtesting/docs/MONITORING_README.md'),
        ('MONTHLY_UPDATE_GUIDE.md', 'backtesting/docs/MONTHLY_UPDATE_GUIDE.md'),
        ('VISUAL_MONITORING_GUIDE.md', 'backtesting/docs/VISUAL_MONITORING_GUIDE.md'),
        
        # Utility scripts
        ('cleanup_workspace.py', 'backtesting/scripts/cleanup_workspace.py'),
        ('cleanup_old_pdfs.py', 'backtesting/scripts/cleanup_old_pdfs.py'),
    ]
    
    print(f"\n🔄 MOVING FILES:")
    print("-" * 40)
    
    moved_files = 0
    total_size = 0
    
    for source, destination in file_moves:
        source_path = Path(source)
        dest_path = Path(destination)
        
        if source_path.exists():
            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get file size
            file_size = source_path.stat().st_size
            
            # Move the file
            shutil.move(str(source_path), str(dest_path))
            
            moved_files += 1
            total_size += file_size
            
            # Format file size
            if file_size >= 1000:
                size_str = f"({file_size / 1000:.1f} KB)"
            else:
                size_str = f"({file_size} bytes)"
            
            print(f"  ✅ {source} → {destination.replace('backtesting/', '')} {size_str}")
        else:
            print(f"  ⚠️  Not found: {source}")
    
    # Move entire directories
    print(f"\n📂 MOVING DIRECTORIES:")
    print("-" * 40)
    
    directory_moves = [
        ('data', 'backtesting/data'),
        ('results', 'backtesting/results'),
        ('archive', 'backtesting/archive'),
    ]
    
    for source_dir, dest_dir in directory_moves:
        source_path = Path(source_dir)
        dest_path = Path(dest_dir)
        
        if source_path.exists() and source_path.is_dir():
            if dest_path.exists():
                # If destination exists, move contents
                for item in source_path.iterdir():
                    dest_item = dest_path / item.name
                    if dest_item.exists():
                        if dest_item.is_dir():
                            shutil.rmtree(dest_item)
                        else:
                            dest_item.unlink()
                    shutil.move(str(item), str(dest_item))
                source_path.rmdir()
            else:
                shutil.move(str(source_path), str(dest_path))
            
            # Count files in moved directory
            file_count = len(list(dest_path.rglob('*'))) if dest_path.exists() else 0
            print(f"  ✅ {source_dir}/ → {dest_dir.replace('backtesting/', '')}/ ({file_count} items)")
        else:
            print(f"  ⚠️  Directory not found: {source_dir}/")
    
    # Remove empty src directory
    src_path = Path('src')
    if src_path.exists() and src_path.is_dir():
        try:
            src_path.rmdir()
            print(f"  🗑️  Removed empty: src/")
        except OSError:
            print(f"  ⚠️  Could not remove src/ (not empty)")
    
    return moved_files, total_size

def create_main_entry_point():
    """Create a main entry point in the root backtesting directory."""
    
    main_script = '''#!/usr/bin/env python3
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
    
    if command == 'analyze':
        print("🚀 Running IBIT strategy analysis...")
        os.chdir(Path(__file__).parent / 'analysis')
        exec(open('analyze.py').read())
        
    elif command == 'update':
        print("📊 Running monthly update...")
        os.chdir(Path(__file__).parent / 'monitoring')
        exec(open('run_monthly_update.py').read())
        
    elif command == 'report':
        print("📄 Generating comprehensive PDF report...")
        os.chdir(Path(__file__).parent / 'analysis')
        exec(open('create_combined_pdf.py').read())
        
    elif command == 'monitor':
        print("📈 Running performance monitoring...")
        os.chdir(Path(__file__).parent / 'monitoring')
        exec(open('monthly_monitor.py').read())
        
    elif command in ['--help', '-h', 'help']:
        print(__doc__)
        
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: analyze, update, report, monitor")
        print("Use 'python main.py --help' for more information")

if __name__ == '__main__':
    main()
'''
    
    main_file = Path('backtesting/main.py')
    main_file.write_text(main_script)
    
    return main_file

def create_readme():
    """Create a comprehensive README for the backtesting folder."""
    
    readme_content = '''# IBIT Backtesting Suite

A comprehensive backtesting and monitoring system for IBIT overnight trading strategy.

## 📁 Project Structure

```
backtesting/
├── main.py                 # Main entry point
├── core/                   # Core strategy implementation
│   ├── strategy.py         # IBIT overnight strategy
│   ├── backtester.py       # Backtesting engine
│   ├── data_fetcher.py     # Market data fetching
│   ├── visualization.py    # Charts and plotting
│   └── config.py           # Configuration settings
├── analysis/               # Analysis scripts
│   ├── analyze.py          # Main analysis script
│   ├── analyze_ibit_spy_strategy.py  # SPY enhancement
│   ├── strategy_comparison.py        # Strategy comparisons
│   └── create_combined_pdf.py       # PDF report generator
├── monitoring/             # Monitoring and automation
│   ├── run_monthly_update.py        # Main update script
│   ├── monthly_update.py            # Update orchestrator
│   ├── monthly_monitor.py           # Performance monitoring
│   └── historical_tracker.py       # Historical analysis
├── data/                   # Market data cache
├── results/                # Analysis outputs and reports
├── docs/                   # Documentation
├── scripts/                # Utility scripts
└── archive/                # Archived files
```

## 🚀 Quick Start

### Run Full Analysis
```bash
cd backtesting
python main.py analyze
```

### Monthly Update
```bash
python main.py update
```

### Generate PDF Report
```bash
python main.py report
```

### Monitor Performance
```bash
python main.py monitor
```

## 📊 Strategy Performance

- **IBIT Overnight Strategy**: 183.8% total return (72.3% annualized)
- **SPY Day Trading Enhancement**: +33.2% improvement
- **Combined Portfolio**: 205.5% total return

## 🔄 Monthly Workflow

1. **Automatic Updates**: Run `python main.py update` monthly
2. **Performance Monitoring**: Track edge persistence with rolling analysis
3. **PDF Reports**: Comprehensive analysis with visualizations
4. **Backup Management**: Automatic backup of previous results

## 📈 Key Features

- Comprehensive backtesting engine
- Risk-adjusted performance metrics
- Rolling performance analysis
- Monthly monitoring automation
- Professional PDF reporting
- SPY day trading enhancement
- Automated backup system

## ⚙️ Configuration

Edit `core/config.py` to modify:
- Initial capital
- Transaction costs
- Date ranges
- Risk parameters

## 📄 Documentation

See `docs/` folder for detailed guides:
- README.md - Main documentation
- MONITORING_README.md - Monitoring setup
- MONTHLY_UPDATE_GUIDE.md - Update procedures
- VISUAL_MONITORING_GUIDE.md - Visualization guide
'''

    readme_file = Path('backtesting/README.md')
    readme_file.write_text(readme_content)
    
    return readme_file

def cleanup_root():
    """Clean up the root directory after reorganization."""
    
    print(f"\n🧹 CLEANING UP ROOT DIRECTORY:")
    print("-" * 40)
    
    # Files to potentially remove from root (now that they're in backtesting/)
    root_path = Path('.')
    
    # Remove any remaining empty directories
    for item in root_path.iterdir():
        if item.is_dir() and item.name not in ['.venv', '.git', 'backtesting']:
            try:
                if not any(item.iterdir()):  # Check if empty
                    item.rmdir()
                    print(f"  🗑️  Removed empty directory: {item.name}/")
            except OSError:
                # Directory not empty, leave it
                pass
    
    print(f"  ✅ Root directory cleanup complete")

def main():
    """Main reorganization function."""
    
    # Check if reorganization already done
    if Path('backtesting').exists() and Path('backtesting/main.py').exists():
        print("⚠️  Backtesting structure already exists!")
        print("🔄 Re-running reorganization will overwrite existing structure.")
        response = input("Continue? (y/N): ").lower()
        if response != 'y':
            print("❌ Reorganization cancelled.")
            return
    
    try:
        # Reorganize files
        moved_files, total_size = reorganize_files()
        
        # Create main entry point
        main_file = create_main_entry_point()
        print(f"\n📝 CREATED ENTRY POINT:")
        print("-" * 40)
        print(f"  ✅ Created: {main_file}")
        
        # Create README
        readme_file = create_readme()
        print(f"  ✅ Created: {readme_file}")
        
        # Cleanup root directory
        cleanup_root()
        
        # Summary
        print(f"\n📊 REORGANIZATION SUMMARY:")
        print("=" * 40)
        print(f"  📁 Structure: Created backtesting/ with 7 subdirectories")
        print(f"  📄 Files moved: {moved_files}")
        
        if total_size >= 1000000:
            size_str = f"{total_size / 1000000:.1f} MB"
        elif total_size >= 1000:
            size_str = f"{total_size / 1000:.1f} KB"
        else:
            size_str = f"{total_size} bytes"
        
        print(f"  💾 Total size: {size_str}")
        print(f"  🚀 Entry point: backtesting/main.py")
        
        print(f"\n✅ REORGANIZATION COMPLETE!")
        print(f"📁 All files organized in: backtesting/")
        print(f"🚀 Quick start: cd backtesting && python main.py analyze")
        
    except Exception as e:
        print(f"\n❌ REORGANIZATION FAILED: {e}")
        print("💡 You may need to manually fix any issues and re-run")

if __name__ == "__main__":
    main()