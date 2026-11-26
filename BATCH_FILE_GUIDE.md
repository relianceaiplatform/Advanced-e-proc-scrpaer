# 🚀 Quick Start Guide - Batch File Setup

## 📁 File Setup

Place these files in `E:\advanced e-Proc scraper\`:

1. **run_scraper.bat** - Automated setup and execution script
2. **tender_scraper_corrected.py** - The main scraper script

Your folder should look like:
```
E:\advanced e-Proc scraper\
├── run_scraper.bat
└── tender_scraper_corrected.py
```

---

## ⚡ Quick Start (First Time)

### Step 1: Double-click `run_scraper.bat`

That's it! The batch file will automatically:
1. ✅ Check if Python is installed
2. ✅ Create a virtual environment
3. ✅ Install all required packages
4. ✅ Install Playwright browser
5. ✅ Ask for your Mistral API key
6. ✅ Run the scraper

### Step 2: Enter Mistral API Key (when prompted)

When you see:
```
Enter your Mistral API key (or press Enter to skip):
```

Paste your Mistral API key from https://console.mistral.ai/

**Note:** You can press Enter to skip, but AI filtering will be disabled.

### Step 3: Confirm to start

When you see:
```
Do you want to start the scraper now (Y/N)?
```

Press `Y` and Enter to start scraping!

---

## 📋 What the Batch File Does

### Phase 1: Environment Setup (First run only)

```
[1/8] Checking Python installation...
      Python version: 3.x.x
      OK!

[2/8] Checking virtual environment...
      Creating virtual environment...
      Virtual environment created successfully!
      OK!

[3/8] Activating virtual environment...
      Virtual environment activated!
      OK!

[4/8] Checking/Installing Python packages...
      Installing required packages...
      Packages installed successfully!
      OK!

[5/8] Checking Playwright browsers...
      Installing Playwright Chromium browser...
      This will download ~100MB - please be patient...
      Chromium browser installed successfully!
      OK!

[6/8] Checking Mistral API Key...
      WARNING: MISTRAL_API_KEY environment variable is not set!
      
      You need a Mistral API key to run the scraper.
      Get one from: https://console.mistral.ai/
      
      Enter your Mistral API key (or press Enter to skip): [YOU ENTER HERE]

[7/8] Checking scraper script...
      Script found: tender_scraper_corrected.py
      OK!

[8/8] Configuration Summary
      ============================================================================
      Script Location:    E:\advanced e-Proc scraper
      Python Version:     3.x.x
      Virtual Environment: ACTIVE
      Packages:           INSTALLED
      Playwright Browser: INSTALLED
      Mistral API Key:    SET
      ============================================================================
```

### Phase 2: Scraping Execution

```
Ready to start scraping!

IMPORTANT NOTES:
- This will scrape 40+ government tender portals
- Estimated runtime: 45-90 minutes
- Output file: NIC_Filtered_Tenders_All_Portals.xlsx
- Log file: scraper_2026-02-12.log

Do you want to start the scraper now (Y/N)? Y

============================================================================
 STARTING TENDER SCRAPER
============================================================================

Starting at: 02/12/2026 10:00:00

[Scraper output will appear here...]

============================================================================
 SCRAPER FINISHED
============================================================================

Finished at: 02/12/2026 11:30:00
Exit code: 0

SUCCESS: Scraper completed successfully!

Output files should be in: E:\advanced e-Proc scraper
- NIC_Filtered_Tenders_All_Portals.xlsx
- scraping_stats_2026-02-12.xlsx
- scraper_2026-02-12.log
```

---

## 🔄 Subsequent Runs

After the first run, the batch file is even faster because:
- ✅ Virtual environment already exists
- ✅ Packages already installed
- ✅ Browser already installed

**Just double-click `run_scraper.bat` again!**

The batch file will:
1. Check everything is still installed
2. Ask if you want to start (Y/N)
3. Run the scraper

---

## 🛠️ Manual Commands (Advanced)

If you prefer to run commands manually:

### One-Time Setup
```batch
cd "E:\advanced e-Proc scraper"
python -m venv venv
venv\Scripts\activate
pip install playwright pandas openpyxl mistralai
python -m playwright install chromium
```

### Set API Key (Permanent - Optional)
```batch
setx MISTRAL_API_KEY "your-api-key-here"
```
*Note: Close and reopen command prompt after this!*

### Run Scraper
```batch
cd "E:\advanced e-Proc scraper"
venv\Scripts\activate
set MISTRAL_API_KEY=your-api-key-here
python tender_scraper_corrected.py
```

---

## ⚙️ Configuration (Optional)

Before running, you can edit `tender_scraper_corrected.py` to change settings:

```python
# Line 18-22: Toggle features
USE_AI_FILTERING = True        # Set to False to disable AI filtering
ENABLE_PHASE_2 = True          # Set to False to skip Work Description extraction
AI_BATCH_SIZE = 20             # Adjust batch size (10-50)
PHASE_2_DELAY = 1              # Seconds between detail page loads
MAX_CONCURRENT_PORTALS = 10    # Number of parallel portals (5-20)
```

### Reduce Concurrency (if your PC struggles):
```python
MAX_CONCURRENT_PORTALS = 5     # Use 5 instead of 10
```

### Test with Single Portal First:
```python
# Line 44: Replace PORTALS with just one
PORTALS = {
    "West Bengal": "https://wbtenders.gov.in/nicgep/app"
}
```

---

## 📊 Output Files

After successful run, you'll find:

### 1. NIC_Filtered_Tenders_All_Portals.xlsx
Main results file with all filtered tenders:
- Portal Source
- S.No.
- Organisation Chain
- Title and Ref.No./Tender ID
- **Work Description** (from details pages!)
- e-Published Date
- Bid Submission Closing Date
- Tender Opening Date
- Details URL
- Identity Hash
- Run Date

**~2,000-2,500 rows** (only unmeaningful titles with descriptions)

### 2. scraping_stats_2026-02-12.xlsx
Statistics per portal:
- portal
- total_extracted
- total_filtered
- phase_2_success
- phase_2_failed
- status
- error (if any)

**40 rows** (one per portal)

### 3. scraper_2026-02-12.log
Detailed execution log with timestamps for debugging

---

## 🐛 Troubleshooting

### "Python is not installed or not in PATH"
**Solution:**
1. Install Python from: https://www.python.org/downloads/
2. **Important:** Check "Add Python to PATH" during installation!
3. Restart command prompt after installation

### "Could not navigate to E:\advanced e-Proc scraper"
**Solution:**
- Verify the folder exists
- Check if you need to change drive letter in `run_scraper.bat` line 17

### "Failed to install packages"
**Solution:**
```batch
cd "E:\advanced e-Proc scraper"
venv\Scripts\activate
pip install --upgrade pip
pip install playwright pandas openpyxl mistralai
```

### "Failed to install Playwright browsers"
**Solution:**
```batch
cd "E:\advanced e-Proc scraper"
venv\Scripts\activate
python -m playwright install --force chromium
```

### API Key Issues
**If you entered the wrong key:**
1. Edit the batch file OR
2. Run manually with correct key:
   ```batch
   cd "E:\advanced e-Proc scraper"
   venv\Scripts\activate
   set MISTRAL_API_KEY=correct-key-here
   python tender_scraper_corrected.py
   ```

**To set permanently:**
```batch
setx MISTRAL_API_KEY "your-api-key-here"
```
*Then close and reopen command prompt!*

### Scraper Crashes/Errors
**Check the log file:**
- Location: `E:\advanced e-Proc scraper\scraper_2026-02-12.log`
- Look for `ERROR` or `FATAL` messages
- Last few lines usually show the problem

**Common issues:**
- Network connectivity problems → Check internet
- Portal website down → Check if website accessible in browser
- Rate limiting → Increase `PHASE_2_DELAY` to 2 or 3 seconds

---

## 💡 Tips

### 1. Run Overnight
The scraper takes 45-90 minutes. Start it before going to bed!

### 2. Test First
Before running all 40 portals, test with just West Bengal:
- Edit `tender_scraper_corrected.py` line 44-48
- Keep only West Bengal portal
- Run the batch file
- Verify output looks correct
- Then restore all portals

### 3. Monitor Progress
Watch the console output to see:
- Which portals are being processed
- Phase 1 completion (extraction + AI filtering)
- Phase 2 progress (Work Description fetching)
- Final statistics

### 4. Check Output Immediately
After completion, open the Excel file right away to verify:
- Tender titles are correct
- Work Descriptions are populated
- Data makes sense

---

## 🔒 API Key Security

**Never share your API key!** It should be kept secret.

**Safe storage options:**
1. **Environment Variable (Recommended):**
   ```batch
   setx MISTRAL_API_KEY "your-key"
   ```

2. **Batch File Prompt (Current method):**
   - Enter each time you run
   - Not stored permanently

3. **Do NOT:**
   - Commit to GitHub
   - Share in screenshots
   - Email to anyone
   - Store in plain text files

---

## 📞 Support

If you encounter issues:

1. Check the log file: `scraper_2026-02-12.log`
2. Review error messages in console
3. Try manual commands (see Advanced section)
4. Check your internet connection
5. Verify Mistral API has credits: https://console.mistral.ai/

---

## ✅ Checklist

Before running, verify:
- [ ] Python installed (3.8 or higher)
- [ ] Files in `E:\advanced e-Proc scraper\`
- [ ] Mistral API key from https://console.mistral.ai/
- [ ] Internet connection active
- [ ] At least 2GB free disk space
- [ ] At least 4GB free RAM

**Then just double-click `run_scraper.bat`!** 🚀
