# Advanced e-Proc Scraper

Multi-portal Indian government e-procurement (NIC/eProc) tender scraper.

## Features

- Scrapes **40+** state and central government tender portals in parallel
- **Phase 1**: Extracts tender listings (title, org, dates, URLs)
- **AI filtering** (optional, via Groq): Keeps only meaningful titles that describe the work
- **Phase 2** (optional): Fetches full Work Description from detail pages
- Isolated sessions per portal (no data bleed)
- Outputs clean Excel report + statistics

## Requirements

- Python 3.9+
- Playwright browsers
- Groq API key (for AI filtering)

## Quick Start (Windows)

1. Place `run_scraper.bat` and `tender_scraper_corrected.py` in the same folder.
2. Double-click `run_scraper.bat`.
3. Follow the prompts (it will create a venv, install packages, and ask for the API key).

## Manual Setup

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install playwright pandas openpyxl groq
playwright install chromium

# Set API key
export GROQ_API_KEY="your_key_here"   # Linux/Mac
set GROQ_API_KEY=your_key_here        # Windows CMD

python tender_scraper_corrected.py
```

## Configuration

Edit the top of `tender_scraper_corrected.py`:

- `USE_AI_FILTERING = True/False`
- `ENABLE_PHASE_2 = True/False`
- `MAX_CONCURRENT_PORTALS = 4` (adjust based on RAM)
- `AI_BATCH_SIZE = 20`

## Output

- `NIC_Filtered_Tenders_All_Portals.xlsx` – filtered tenders
- `scraping_stats_YYYY-MM-DD.xlsx` – per-portal statistics
- `scraper_YYYY-MM-DD.log` – detailed log

## Notes

- Do **not** commit API keys or the `venv` folder.
- The batch file hard-codes a Windows path (`E:\advanced e-Proc scraper`). Edit it if needed.
