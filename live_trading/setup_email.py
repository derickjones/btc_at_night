#!/usr/bin/env python3
"""
Email Setup and Test Script for IBIT Trading Strategy
Helps configure Gmail App Password and tests email functionality.
"""

import sys
from pathlib import Path
import getpass

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from monitor import PerformanceMonitor
from config import EMAIL_FROM, EMAIL_RECIPIENTS

def update_config_with_app_password():
    """Help user update config with Gmail App Password."""
    config_file = Path(__file__).parent / 'config.py'
    
    print("\n🔧 Gmail App Password Setup")
    print("="*50)
    print("To send daily email reports, you need a Gmail App Password.")
    print("\nSteps to get your App Password:")
    print("1. Go to https://myaccount.google.com/security")
    print("2. Enable 2-Step Verification (if not already enabled)")
    print("3. Go to 'App passwords' section")
    print("4. Generate a new app password for 'Mail'")
    print("5. Copy the 16-character password (no spaces)")
    
    app_password = getpass.getpass("\nEnter your Gmail App Password (16 characters): ")
    
    if len(app_password) != 16:
        print("❌ App Password should be 16 characters long")
        return False
    
    # Read current config
    with open(config_file, 'r') as f:
        config_content = f.read()
    
    # Replace the EMAIL_APP_PASSWORD line
    lines = config_content.split('\n')
    for i, line in enumerate(lines):
        if 'EMAIL_APP_PASSWORD = None' in line:
            lines[i] = f'EMAIL_APP_PASSWORD = "{app_password}"  # Gmail App Password'
            break
    
    # Write back to file
    with open(config_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print("✅ App Password saved to config.py")
    return True

def test_email_configuration():
    """Test email configuration by sending a test email."""
    print("\n📧 Testing Email Configuration")
    print("="*40)
    
    try:
        monitor = PerformanceMonitor()
        
        # Create a test email
        test_subject = "IBIT Strategy - Email Test"
        test_body = f"""
This is a test email from your IBIT Trading Strategy system.

Configuration:
- Email From: {EMAIL_FROM}
- Email Recipients: {', '.join(EMAIL_RECIPIENTS)}
- Timestamp: {monitor.generate_daily_report().split('/')[-1].replace('.txt', '')}

If you receive this email, daily reports are configured correctly! ✅

Next steps:
1. Run your trading strategy: python strategy.py
2. Generate daily reports: python daily_email_report.py
3. Schedule daily reports with cron (see daily_email_report.py for example)
"""
        
        success = monitor.send_email_report(
            subject=test_subject,
            body=test_body
        )
        
        if success:
            print("✅ Test email sent successfully!")
            print(f"📬 Check your inbox: {', '.join(EMAIL_RECIPIENTS)}")
            return True
        else:
            print("❌ Failed to send test email")
            return False
            
    except Exception as e:
        print(f"❌ Error testing email: {e}")
        return False

def main():
    """Main setup and test function."""
    print("🚀 IBIT Strategy Email Setup")
    print("="*50)
    
    print(f"📧 Current email configuration:")
    print(f"   From: {EMAIL_FROM}")
    print(f"   To: {', '.join(EMAIL_RECIPIENTS)}")
    
    choice = input("\nWhat would you like to do?\n1. Set up Gmail App Password\n2. Test email configuration\n3. Both\nEnter choice (1-3): ")
    
    if choice in ['1', '3']:
        if not update_config_with_app_password():
            return
        print("\n" + "="*50)
    
    if choice in ['2', '3']:
        # Need to reload config after password update
        if choice == '3':
            print("Reloading configuration...")
            # Force reload of config module
            import importlib
            import config
            importlib.reload(config)
        
        success = test_email_configuration()
        
        if success:
            print("\n🎉 Email setup complete!")
            print("\n📋 Usage:")
            print("• Manual report: python monitor.py --email")
            print("• Daily automated: python daily_email_report.py")
            print("• Schedule with cron: 30 17 * * 1-5 cd $(pwd) && python daily_email_report.py")
        else:
            print("\n❌ Email setup incomplete. Please check your configuration.")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    main()