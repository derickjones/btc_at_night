# IBIT Strategy Monthly Update Guide

## 📅 How to Update Your Strategy Analysis Monthly

Your IBIT overnight strategy analysis should be updated monthly to:
- ✅ Include latest trading data
- ✅ Track strategy edge persistence/decay  
- ✅ Update rolling performance metrics
- ✅ Refresh SPY day trading analysis
- ✅ Generate updated PDF reports

---

## 🚀 Simple Monthly Update (Recommended)

**Run this command monthly:**

```bash
python run_monthly_update.py
```

This will:
1. 📁 Backup your current results
2. 📊 Fetch latest IBIT data 
3. 🚀 Run strategy analysis
4. 📈 Update SPY analysis
5. 📊 Run monthly monitoring
6. 📄 Generate updated PDF report

**Expected time: 2-3 minutes**

---

## ⚙️ Advanced Update Options

### Full Reanalysis (Monthly Recommended)
```bash
python monthly_update.py --full-reanalysis --generate-pdf
```

### Quick Update (Weekly Check)
```bash
python monthly_update.py --quick
```

### PDF Only (If you just want updated report)
```bash
python create_combined_pdf.py
```

---

## 🤖 Automated Monthly Updates

### Option 1: macOS Automator (Easy)

1. Open **Automator** app
2. Create new **Calendar Alarm**
3. Add **Run Shell Script** action
4. Set shell to `/bin/bash`
5. Add script:
   ```bash
   cd /Users/derickjones/Documents/VS-Code/btc_at_night
   /Users/derickjones/Documents/VS-Code/btc_at_night/.venv/bin/python run_monthly_update.py
   ```
6. Save and set monthly reminder

### Option 2: Cron Job (Advanced)

1. Open terminal and run: `crontab -e`
2. Add this line for monthly updates (1st of each month at 9 AM):
   ```bash
   0 9 1 * * cd /Users/derickjones/Documents/VS-Code/btc_at_night && /Users/derickjones/Documents/VS-Code/btc_at_night/.venv/bin/python run_monthly_update.py
   ```

### Option 3: Calendar Reminder (Simple)

Set a monthly calendar reminder to manually run:
```bash
python run_monthly_update.py
```

---

## 📊 What Gets Updated

### 📈 Core Analysis
- **Trade Results**: Latest IBIT overnight trades
- **Performance Metrics**: Updated returns, Sharpe ratio, drawdown
- **Rolling Analysis**: Edge persistence/decay tracking

### 📊 Rolling Performance Charts  
- **6-Panel Analysis**: Returns, win rates, Sharpe ratios, edge scores
- **Trend Analysis**: Portfolio growth with recent vs historical trends
- **Health Assessment**: Strategy status (IMPROVING/STABLE/DETERIORATING)

### 💰 SPY Enhancement
- **Combined Strategy**: IBIT overnight + SPY day trading
- **Performance Comparison**: Updated enhancement metrics
- **Risk Analysis**: Combined strategy drawdown and volatility

### 📄 PDF Report
- **Complete Analysis**: All charts and metrics in one document
- **Monthly Insights**: New performance trends and recommendations
- **Backup History**: Previous reports saved automatically

---

## 🔍 Monitoring Your Updates

### Check Last Update
```bash
cat results/last_update.json
```

### View Monthly Monitoring Results
```bash
ls results/monthly_monitoring/
```

### Check PDF Report
- **Main Report**: `results/IBIT_Strategy_Complete_Analysis.pdf`
- **File Size**: ~3-4MB with all charts
- **Content**: Complete analysis + rolling charts + SPY enhancement

### Review Backups
```bash
ls results/backups/
```

---

## 🚨 Troubleshooting

### If Update Fails
1. Check internet connection (needs market data)
2. Verify Python environment: `source .venv/bin/activate`
3. Run manual steps:
   ```bash
   python analyze.py                    # Core analysis
   python analyze_ibit_spy_strategy.py  # SPY enhancement  
   python create_combined_pdf.py        # PDF report
   ```

### Data Issues
- **No new data**: Markets might be closed or data provider issue
- **Incomplete data**: Re-run with `--full-reanalysis` flag
- **Old data**: Check if yfinance is working: `pip install -U yfinance`

### PDF Generation Issues
- **Missing charts**: Run `python create_combined_pdf.py` separately
- **Large file size**: Normal for comprehensive analysis with charts
- **Formatting issues**: Check reportlab installation

---

## 📅 Recommended Schedule

- **Monthly**: Full update with `python run_monthly_update.py`
- **Quarterly**: Review strategy performance trends
- **Yearly**: Consider strategy parameter optimization

---

## 💡 Pro Tips

1. **Run updates after market close** for complete daily data
2. **Check the rolling performance charts** for edge persistence
3. **Monitor the strategy health assessment** for early warning signs
4. **Compare monthly results** to track performance trends
5. **Backup important reports** before major updates

---

## 📧 Update Checklist

After each monthly update, verify:

- [ ] New trade data included
- [ ] Rolling charts show recent performance  
- [ ] Strategy health assessment updated
- [ ] SPY enhancement metrics refreshed
- [ ] PDF report generated successfully
- [ ] Backup created automatically

**Your strategy analysis stays current and actionable!** 🎯