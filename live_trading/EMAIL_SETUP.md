# Daily Email Reports Setup Guide

Your IBIT trading strategy now supports automatic daily email reports! Here's how to set it up and use it.

## 🚀 Quick Setup

1. **Run the email setup script:**
   ```bash
   python setup_email.py
   ```

2. **Follow the prompts to:**
   - Set up your Gmail App Password
   - Test email configuration
   - Verify everything works

## 📧 Gmail App Password Setup

To send emails through Gmail, you need an App Password:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (if not already enabled)
3. Go to **App passwords** section
4. Generate a new app password for **Mail**
5. Copy the 16-character password (no spaces)
6. Use this password in the setup script

## 📋 Usage Options

### Manual Email Report
Send a one-time email report:
```bash
python monitor.py --email
```

### Daily Automated Report
Send today's report (for cron scheduling):
```bash
python daily_email_report.py
```

### Local Report Only
Generate report without email:
```bash
python monitor.py
```

## ⏰ Automatic Daily Reports

To receive daily reports automatically, set up a scheduled task:

### macOS/Linux (cron)
```bash
# Edit your crontab
crontab -e

# Add this line (runs at 5:30 PM Monday-Friday)
30 17 * * 1-5 cd /path/to/your/live_trading && python daily_email_report.py
```

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 5:30 PM
4. Set action: Run `python daily_email_report.py`
5. Set working directory: your `live_trading` folder

## 📊 What's Included in Email Reports

Each daily email contains:

✅ **Performance Summary:**
- Total trades and win rate
- Total P&L and average per trade
- Best and worst trades

✅ **Risk Metrics:**
- Sharpe ratio and volatility
- Profit factor
- Consecutive wins/losses

✅ **Recent Activity:**
- Last 5 trades with P&L
- Trade status and timing

✅ **Performance Chart:**
- Visual portfolio performance
- Individual trade P&L
- P&L distribution
- Win/loss pie chart

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Email Settings
ENABLE_DAILY_EMAIL_REPORTS = True
EMAIL_RECIPIENTS = ['your_email@gmail.com']
EMAIL_FROM = 'your_gmail@gmail.com'
EMAIL_APP_PASSWORD = 'your_16_char_app_password'

# Timing
DAILY_REPORT_TIME_HOUR = 17  # 5 PM
DAILY_REPORT_TIME_MINUTE = 30
```

## 🛠️ Troubleshooting

### Email Not Sending?
1. Check your Gmail App Password (16 characters)
2. Verify 2-Step Verification is enabled
3. Check `logs/` folder for error messages
4. Run `python setup_email.py` to test configuration

### Wrong Email Address?
Update `EMAIL_RECIPIENTS` in `config.py`:
```python
EMAIL_RECIPIENTS = ['new_email@example.com']
```

### Multiple Recipients?
Add multiple emails:
```python
EMAIL_RECIPIENTS = ['email1@gmail.com', 'email2@yahoo.com']
```

## 📁 File Structure

```
live_trading/
├── monitor.py              # Main monitoring (python monitor.py --email)
├── daily_email_report.py   # Daily scheduler (for cron)
├── setup_email.py          # Setup and test tool
├── config.py               # Email configuration
└── logs/
    ├── daily_email_*.log    # Email sending logs
    └── email_log.txt        # Email history
```

## 🎯 Next Steps

1. **Run setup:** `python setup_email.py`
2. **Test manually:** `python monitor.py --email`
3. **Schedule daily:** Add cron job or Windows task
4. **Start trading:** `python strategy.py`
5. **Monitor performance:** Check your daily emails! 📬

Your trading performance reports will now arrive in your inbox every day after market close! 📈✉️