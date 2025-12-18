"""
Performance Monitor for Live IBIT Trading Strategy
Monitors and reports on live trading performance with daily email reports.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import logging

from config import (
    RESULTS_DIR, EMAIL_RECIPIENTS, ENABLE_EMAIL_ALERTS,
    ENABLE_DAILY_EMAIL_REPORTS, EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT,
    EMAIL_FROM, EMAIL_APP_PASSWORD
)


class PerformanceMonitor:
    """Monitor and analyze live trading performance."""
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.trades_file = RESULTS_DIR / 'live_trades.json'
        self.performance_file = RESULTS_DIR / 'live_performance.json'
        self.reports_dir = RESULTS_DIR / 'reports'
        self.reports_dir.mkdir(exist_ok=True)
    
    def load_trade_data(self) -> pd.DataFrame:
        """Load trade history from file."""
        if not self.trades_file.exists():
            return pd.DataFrame()
        
        with open(self.trades_file, 'r') as f:
            trades = json.load(f)
        
        if not trades:
            return pd.DataFrame()
        
        df = pd.DataFrame(trades)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    def calculate_performance_metrics(self) -> dict:
        """Calculate comprehensive performance metrics."""
        trades_df = self.load_trade_data()
        
        if trades_df.empty:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_pnl_per_trade': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'consecutive_wins': 0,
                'consecutive_losses': 0,
                'sharpe_ratio': 0,
                'volatility': 0
            }
        
        # Filter completed trades with P&L
        completed_trades = trades_df[trades_df['status'] == 'filled'].copy()
        pnl_trades = completed_trades[completed_trades['pnl'].notna()].copy()
        
        if pnl_trades.empty:
            return {'total_trades': len(completed_trades), 'status': 'no_completed_cycles'}
        
        # Basic metrics
        total_pnl = pnl_trades['pnl'].sum()
        winning_trades = (pnl_trades['pnl'] > 0).sum()
        losing_trades = (pnl_trades['pnl'] < 0).sum()
        total_trades = len(pnl_trades)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Advanced metrics
        avg_pnl = pnl_trades['pnl'].mean()
        best_trade = pnl_trades['pnl'].max()
        worst_trade = pnl_trades['pnl'].min()
        
        # Risk metrics
        volatility = pnl_trades['pnl'].std()
        sharpe_ratio = avg_pnl / volatility if volatility > 0 else 0
        
        # Consecutive wins/losses
        pnl_trades['win'] = pnl_trades['pnl'] > 0
        consecutive_wins = self._calculate_max_consecutive(pnl_trades['win'], True)
        consecutive_losses = self._calculate_max_consecutive(pnl_trades['win'], False)
        
        return {
            'total_trades': total_trades,
            'winning_trades': int(winning_trades),
            'losing_trades': int(losing_trades),
            'win_rate': float(win_rate),
            'total_pnl': float(total_pnl),
            'avg_pnl_per_trade': float(avg_pnl),
            'best_trade': float(best_trade),
            'worst_trade': float(worst_trade),
            'consecutive_wins': int(consecutive_wins),
            'consecutive_losses': int(consecutive_losses),
            'sharpe_ratio': float(sharpe_ratio),
            'volatility': float(volatility),
            'profit_factor': float(abs(pnl_trades[pnl_trades['pnl'] > 0]['pnl'].mean() / 
                                    pnl_trades[pnl_trades['pnl'] < 0]['pnl'].mean())) 
                            if losing_trades > 0 else float('inf')
        }
    
    def _calculate_max_consecutive(self, series: pd.Series, target_value: bool) -> int:
        """Calculate maximum consecutive occurrences of target value."""
        if series.empty:
            return 0
        
        max_consecutive = 0
        current_consecutive = 0
        
        for value in series:
            if value == target_value:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def create_performance_chart(self, save_path: Path = None) -> str:
        """Create performance visualization chart."""
        trades_df = self.load_trade_data()
        
        if trades_df.empty:
            print("No trade data available for charting")
            return None
        
        # Filter trades with P&L
        pnl_trades = trades_df[trades_df['pnl'].notna()].copy()
        if pnl_trades.empty:
            print("No P&L data available for charting")
            return None
        
        # Calculate cumulative P&L
        pnl_trades = pnl_trades.sort_values('timestamp')
        pnl_trades['cumulative_pnl'] = pnl_trades['pnl'].cumsum()
        
        # Create the chart
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Cumulative P&L
        ax1.plot(pnl_trades['timestamp'], pnl_trades['cumulative_pnl'], 
                linewidth=2, color='blue')
        ax1.set_title('Cumulative P&L Over Time')
        ax1.set_ylabel('Cumulative P&L ($)')
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # Individual trade P&L
        colors = ['green' if x > 0 else 'red' for x in pnl_trades['pnl']]
        ax2.bar(range(len(pnl_trades)), pnl_trades['pnl'], color=colors, alpha=0.7)
        ax2.set_title('Individual Trade P&L')
        ax2.set_xlabel('Trade Number')
        ax2.set_ylabel('P&L ($)')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # P&L Distribution
        ax3.hist(pnl_trades['pnl'], bins=20, alpha=0.7, color='purple', edgecolor='black')
        ax3.set_title('P&L Distribution')
        ax3.set_xlabel('P&L ($)')
        ax3.set_ylabel('Frequency')
        ax3.axvline(pnl_trades['pnl'].mean(), color='red', linestyle='--', 
                   label=f'Mean: ${pnl_trades["pnl"].mean():.2f}')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Win/Loss Analysis
        wins = (pnl_trades['pnl'] > 0).sum()
        losses = (pnl_trades['pnl'] < 0).sum()
        neutral = (pnl_trades['pnl'] == 0).sum()
        
        ax4.pie([wins, losses, neutral], 
               labels=['Wins', 'Losses', 'Neutral'], 
               colors=['green', 'red', 'gray'],
               autopct='%1.1f%%',
               startangle=90)
        ax4.set_title('Win/Loss Distribution')
        
        plt.tight_layout()
        
        # Save chart
        if save_path is None:
            save_path = self.reports_dir / f'performance_chart_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return str(save_path)
    
    def generate_daily_report(self) -> str:
        """Generate daily performance report."""
        metrics = self.calculate_performance_metrics()
        trades_df = self.load_trade_data()
        
        report_time = datetime.now()
        
        report = f"""
IBIT Overnight Strategy - Daily Performance Report
Generated: {report_time.strftime("%Y-%m-%d %H:%M:%S")}
{'='*60}

PERFORMANCE SUMMARY:
  Total Trades: {metrics['total_trades']}
  Win Rate: {metrics['win_rate']:.1%}
  Total P&L: ${metrics['total_pnl']:.2f}
  Average P&L per Trade: ${metrics['avg_pnl_per_trade']:.2f}
  Best Trade: ${metrics['best_trade']:.2f}
  Worst Trade: ${metrics['worst_trade']:.2f}

RISK METRICS:
  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}
  Volatility: ${metrics.get('volatility', 0):.2f}
  Profit Factor: {metrics.get('profit_factor', 0):.2f}
  Max Consecutive Wins: {metrics['consecutive_wins']}
  Max Consecutive Losses: {metrics['consecutive_losses']}

RECENT ACTIVITY:
"""
        
        # Add recent trades
        if not trades_df.empty:
            recent_trades = trades_df.tail(5)
            for _, trade in recent_trades.iterrows():
                report += f"  {trade.get('timestamp', 'N/A')}: {trade.get('action', 'N/A').upper()} "
                report += f"{trade.get('shares', 0)} shares"
                if 'pnl' in trade and pd.notna(trade['pnl']):
                    report += f" - P&L: ${trade['pnl']:.2f}"
                report += f" (Status: {trade.get('status', 'N/A')})\n"
        else:
            report += "  No trades executed yet\n"
        
        report += f"\n{'='*60}\n"
        
        # Save report
        report_file = self.reports_dir / f'daily_report_{report_time.strftime("%Y%m%d")}.txt'
        with open(report_file, 'w') as f:
            f.write(report)
        
        return str(report_file)
    
    def send_email_report(self, subject: str, body: str, chart_path: str = None) -> bool:
        """Send email report with optional chart attachment."""
        if not ENABLE_DAILY_EMAIL_REPORTS or not EMAIL_FROM or not EMAIL_APP_PASSWORD:
            print("📧 Email reporting not configured or disabled")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = EMAIL_FROM
            msg['To'] = ', '.join(EMAIL_RECIPIENTS)
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add chart if provided
            if chart_path and Path(chart_path).exists():
                with open(chart_path, 'rb') as f:
                    chart_data = f.read()
                
                chart_attachment = MIMEImage(chart_data)
                chart_attachment.add_header('Content-Disposition', 
                                          f'attachment; filename="performance_chart.png"')
                msg.attach(chart_attachment)
            
            # Send email
            server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_APP_PASSWORD)
            
            for recipient in EMAIL_RECIPIENTS:
                server.sendmail(EMAIL_FROM, recipient, msg.as_string())
            
            server.quit()
            print(f"📧 Daily report sent to {len(EMAIL_RECIPIENTS)} recipient(s)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            logging.error(f"Email send failed: {e}")
            return False
    
    def generate_and_send_daily_report(self) -> bool:
        """Generate daily report and send via email."""
        try:
            # Generate report file
            report_file = self.generate_daily_report()
            
            # Create performance chart
            chart_file = self.create_performance_chart()
            
            # Read report content
            with open(report_file, 'r') as f:
                report_content = f.read()
            
            # Create email subject
            today = datetime.now().strftime("%Y-%m-%d")
            metrics = self.calculate_performance_metrics()
            subject = f"IBIT Strategy Daily Report - {today} (P&L: ${metrics['total_pnl']:.2f})"
            
            # Send email with chart
            success = self.send_email_report(
                subject=subject,
                body=report_content,
                chart_path=chart_file
            )
            
            if success:
                print(f"✅ Daily email report sent successfully")
                # Log the email send
                with open(self.reports_dir / 'email_log.txt', 'a') as f:
                    f.write(f"{datetime.now()}: Daily report sent\n")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to generate and send daily report: {e}")
            logging.error(f"Daily report generation failed: {e}")
            return False
    
    def print_status(self):
        """Print current strategy status to console."""
        metrics = self.calculate_performance_metrics()
        
        print("\n" + "="*50)
        print("IBIT OVERNIGHT STRATEGY - LIVE STATUS")
        print("="*50)
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Win Rate: {metrics['win_rate']:.1%}")
        print(f"Total P&L: ${metrics['total_pnl']:.2f}")
        print(f"Avg P&L per Trade: ${metrics['avg_pnl_per_trade']:.2f}")
        print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)


def main():
    """Generate performance report and optionally send email."""
    import argparse
    
    parser = argparse.ArgumentParser(description='IBIT Strategy Performance Monitor')
    parser.add_argument('--email', action='store_true', 
                       help='Send daily report via email')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress console output')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor()
    
    if not args.quiet:
        print("📊 Generating performance report...")
    
    if args.email:
        # Generate and send email report
        success = monitor.generate_and_send_daily_report()
        if not success and not args.quiet:
            print("❌ Failed to send email report")
    else:
        # Generate local report only
        report_file = monitor.generate_daily_report()
        if not args.quiet:
            print(f"✅ Daily report saved: {report_file}")
        
        # Create performance chart
        chart_file = monitor.create_performance_chart()
        if chart_file and not args.quiet:
            print(f"✅ Performance chart saved: {chart_file}")
    
    # Print status (unless quiet)
    if not args.quiet:
        monitor.print_status()


if __name__ == "__main__":
    main()