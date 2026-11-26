set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
chcp 65001 >nul

@echo off
REM ============================================================================
REM  Tender Scraper - Complete Setup and Run Script
REM  Location: E:\advanced e-Proc scraper
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo  TENDER SCRAPER - AUTOMATED SETUP AND EXECUTION
echo ============================================================================
echo.

REM Navigate to script directory
cd /d "E:\advanced e-Proc scraper"
if errorlevel 1 (
    echo ERROR: Could not navigate to E:\advanced e-Proc scraper
    echo Please verify the folder exists!
    pause
    exit /b 1
)

echo [1/8] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo    Python version: %PYTHON_VERSION%
echo    OK!
echo.

REM ============================================================================
REM  VIRTUAL ENVIRONMENT SETUP
REM ============================================================================

echo [2/8] Checking virtual environment...
if exist "venv\Scripts\activate.bat" (
    echo    Virtual environment exists - checking if valid...
    
    REM Test if the venv is working
    call venv\Scripts\activate.bat
    python -c "import sys; print('OK')" >nul 2>&1
    if errorlevel 1 (
        echo    Virtual environment appears corrupted!
        echo    Deleting and recreating...
        call venv\Scripts\deactivate.bat 2>nul
        rmdir /s /q venv
        python -m venv venv
        if errorlevel 1 (
            echo    ERROR: Failed to create virtual environment!
            pause
            exit /b 1
        )
        echo    Virtual environment recreated successfully!
    ) else (
        echo    Virtual environment is valid!
    )
    echo    OK!
) else (
    echo    Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo    ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo    Virtual environment created successfully!
    echo    OK!
)
echo.

echo [3/8] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo    ERROR: Failed to activate virtual environment!
    pause
    exit /b 1
)
echo    Virtual environment activated!
echo    OK!
echo.

REM ============================================================================
REM  DEPENDENCY INSTALLATION
REM ============================================================================

echo [4/8] Installing Python packages...
echo    This may take a few minutes...
echo.

REM Always check and install if needed - don't skip
python -c "import playwright, pandas, openpyxl, mistralai" >nul 2>&1
if errorlevel 1 (
    echo    One or more packages missing - installing all...
    echo.
    
    REM Upgrade pip first
    echo    Upgrading pip...
    python -m pip install --upgrade pip
    echo.
    
    REM Install all packages at once
    echo    Installing: playwright, pandas, openpyxl, mistralai...
    pip install playwright pandas openpyxl mistralai
    if errorlevel 1 (
        echo.
        echo    ERROR: Package installation failed!
        echo.
        echo    Please try manually:
        echo    1. cd "E:\advanced e-Proc scraper"
        echo    2. venv\Scripts\activate
        echo    3. pip install playwright pandas openpyxl mistralai
        echo.
        pause
        exit /b 1
    )
    
    echo.
    echo    Packages installed successfully!
) else (
    echo    All packages already installed!
)
echo    OK!
echo.

REM ============================================================================
REM  PLAYWRIGHT BROWSER INSTALLATION
REM ============================================================================

echo [5/8] Installing Playwright browsers...
echo    This will download ~100-150MB on first run...
echo.

REM Check if playwright module exists before trying to use it
python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo    ERROR: Playwright package is not installed!
    echo    Something went wrong in the previous step.
    echo.
    echo    Please run manually:
    echo    1. cd "E:\advanced e-Proc scraper"
    echo    2. venv\Scripts\activate
    echo    3. pip install playwright
    echo    4. python -m playwright install chromium
    echo.
    pause
    exit /b 1
)

echo    Installing Chromium browser...
python -m playwright install chromium

if errorlevel 1 (
    echo.
    echo    ERROR: Failed to install Playwright browsers!
    echo.
    echo    Troubleshooting:
    echo    1. Check your internet connection
    echo    2. Make sure you have at least 200MB free disk space
    echo    3. Try running manually: python -m playwright install chromium
    echo.
    pause
    exit /b 1
)

echo.
echo    Chromium browser installed successfully!
echo    OK!
echo.

REM ============================================================================
REM  MISTRAL API KEY SETUP
REM ============================================================================

echo [6/8] Checking Mistral API Key...

if defined MISTRAL_API_KEY (
    echo    MISTRAL_API_KEY is already set!
    echo    Key: %MISTRAL_API_KEY:~0,8%...%MISTRAL_API_KEY:~-4%
    echo    OK!
) else (
    echo.
    echo    WARNING: MISTRAL_API_KEY environment variable is not set!
    echo.
    echo    You need a Mistral API key to run the scraper.
    echo    Get one from: https://console.mistral.ai/
    echo.
    set /p API_KEY="    Enter your Mistral API key (or press Enter to skip): "
    
    if defined API_KEY (
        set MISTRAL_API_KEY=!API_KEY!
        echo    API key set for this session!
        echo    OK!
    ) else (
        echo.
        echo    WARNING: No API key provided!
        echo    The scraper will run WITHOUT AI filtering!
        echo    Press any key to continue anyway, or Ctrl+C to exit...
        pause >nul
    )
)
echo.

REM ============================================================================
REM  VERIFY SCRIPT EXISTS
REM ============================================================================

echo [7/8] Checking scraper script...

if exist "tender_scraper_corrected.py" (
    echo    Script found: tender_scraper_corrected.py
    echo    OK!
) else (
    echo.
    echo    ERROR: tender_scraper_corrected.py not found!
    echo    Please make sure the script is in: E:\advanced e-Proc scraper
    echo.
    pause
    exit /b 1
)
echo.

REM ============================================================================
REM  CONFIGURATION SUMMARY
REM ============================================================================

echo [8/8] Configuration Summary
echo ============================================================================
echo    Script Location:    E:\advanced e-Proc scraper
echo    Python Version:     %PYTHON_VERSION%
echo    Virtual Environment: ACTIVE
echo    Packages:           INSTALLED
echo    Playwright Browser: INSTALLED
if defined MISTRAL_API_KEY (
    echo    Mistral API Key:    SET
) else (
    echo    Mistral API Key:    NOT SET (AI filtering disabled)
)
echo ============================================================================
echo.

REM ============================================================================
REM  FINAL CONFIRMATION
REM ============================================================================

echo Ready to start scraping!
echo.
echo IMPORTANT NOTES:
echo - This will scrape 40+ government tender portals
echo - Estimated runtime: 45-90 minutes
echo - Output file: NIC_Filtered_Tenders_All_Portals.xlsx
echo - Log file: scraper_%date:~-4,4%-%date:~-7,2%-%date:~-10,2%.log
echo.

choice /C YN /M "Do you want to start the scraper now"
if errorlevel 2 (
    echo.
    echo Scraper launch cancelled.
    echo.
    echo To run the scraper later, use:
    echo    cd "E:\advanced e-Proc scraper"
    echo    venv\Scripts\activate
    echo    python tender_scraper_corrected.py
    echo.
    pause
    exit /b 0
)

REM ============================================================================
REM  RUN THE SCRAPER
REM ============================================================================

echo.
echo ============================================================================
echo  STARTING TENDER SCRAPER
echo ============================================================================
echo.
echo Starting at: %date% %time%
echo.

python tender_scraper_corrected.py

REM Capture exit code
set SCRAPER_EXIT_CODE=%errorlevel%

echo.
echo ============================================================================
echo  SCRAPER FINISHED
echo ============================================================================
echo.
echo Finished at: %date% %time%
echo Exit code: %SCRAPER_EXIT_CODE%
echo.

if %SCRAPER_EXIT_CODE% equ 0 (
    echo SUCCESS: Scraper completed successfully!
    echo.
    echo Output files should be in: E:\advanced e-Proc scraper
    echo - NIC_Filtered_Tenders_All_Portals.xlsx
    echo - scraping_stats_%date:~-4,4%-%date:~-7,2%-%date:~-10,2%.xlsx
    echo - scraper_%date:~-4,4%-%date:~-7,2%-%date:~-10,2%.log
) else (
    echo ERROR: Scraper encountered an error!
    echo Check the log file for details: scraper_%date:~-4,4%-%date:~-7,2%-%date:~-10,2%.log
)

echo.
pause

endlocal