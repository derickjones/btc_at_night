#!/usr/bin/env python3
"""
IBIT Strategy Monthly Monitoring Script
=====================================

This script runs the complete monthly analysis workflow to track:
1. Current strategy performance vs baseline (72.3% annual, 1.81 Sharpe)
2. Trade pattern analysis and win rate trends
3. Performance degradation alerts
4. Historical trend analysis across multiple months
5. Edge persistence evaluation

Usage:
    python run_monthly_check.py

The script will:
- Fetch latest IBIT data (90 days)
- Run backtest with current strategy
- Compare performance against baseline metrics
- Generate executive summary with actionable insights
- Update historical tracking database
- Create performance visualizations
- Assess long-term edge persistence

Output:
- Monthly performance report (JSON)
- Performance charts (PNG)
- Historical dashboard (PNG)  
- Console executive summary
- Performance history database (CSV)

Recommended: Run monthly to maintain edge detection capability.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.append('.')

from monthly_monitor import run_monthly_monitoring

def main():
    """Run the complete monthly monitoring workflow."""
    
    print("🔍 IBIT Strategy Monthly Performance Check")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Purpose: Edge persistence monitoring and performance tracking")
    print("=" * 60)
    
    # Run monitoring
    results = run_monthly_monitoring()
    
    if results:
        monthly_report = results['monthly_report']
        total_months = results['total_months_tracked']
        
        print("\n📋 QUICK SUMMARY:")
        print("=" * 30)
        
        # Extract key metrics
        recent_return = monthly_report['performance_analysis']['recent_metrics']['annual_return']
        recent_sharpe = monthly_report['performance_analysis']['recent_metrics']['sharpe_ratio']
        vs_baseline = monthly_report['performance_analysis']['vs_baseline']['return_diff']
        flags = len(monthly_report['performance_analysis']['performance_flags'])
        
        print(f"📈 Recent Performance:")
        print(f"   Annual Return: {recent_return:.1%} (vs 72.3% baseline)")
        print(f"   Sharpe Ratio: {recent_sharpe:.2f} (vs 1.81 baseline)")
        print(f"   Outperformance: {vs_baseline:+.1%}")
        
        print(f"\n🚩 Performance Flags: {flags}")
        if flags > 0:
            print("   ⚠️  Review detailed analysis for concerns")
        else:
            print("   ✅ No performance concerns detected")
        
        print(f"\n📊 Historical Tracking: {total_months} months of data")
        
        if results.get('historical_analysis'):
            hist = results['historical_analysis']
            persistence_rate = hist['stability_metrics']['edge_persistence_rate']
            print(f"   Edge Persistence Rate: {persistence_rate:.1%}")
            
            if persistence_rate > 0.7:
                print("   🟢 Strategy edge appears strong and persistent")
            elif persistence_rate > 0.5:
                print("   🟡 Strategy shows edge but monitor for degradation")  
            else:
                print("   🔴 Strategy edge may be deteriorating - investigate")
        
        print(f"\n📁 Results Location:")
        print(f"   Monthly Reports: results/monthly_monitoring/")
        print(f"   Historical Data: results/monthly_monitoring/performance_history.csv")
        print(f"   Charts: results/monthly_monitoring/*.png")
        
        print(f"\n💡 Next Actions:")
        print(f"   - Review detailed monthly report for insights")
        print(f"   - Check performance charts for visual trends") 
        print(f"   - Run again next month for continued tracking")
        
        if flags > 0:
            print(f"   ⚠️  PRIORITY: Investigate performance flags in detailed report")
        
        print("\n🎯 Monitoring Status: COMPLETE ✅")
        
    else:
        print("\n❌ Monitoring failed - check error messages above")
        print("💡 Common issues:")
        print("   - Market data connectivity")
        print("   - Missing dependencies") 
        print("   - Insufficient historical data")
        
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)