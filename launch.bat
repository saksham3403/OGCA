@echo off
REM Expense Tracker Pro - Windows Launcher Script
REM This script will start the Expense Tracker Pro application

title Expense Tracker Pro
color 1E

cls
echo.
echo =====================================================
echo.
echo     ^| ^| -   EXPENSE TRACKER PRO   -  ^| ^| 
echo.    
echo     Professional Finance Management
echo.
echo =====================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python 3.7+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo [INFO] Checking dependencies...
python -c "import reportlab; import PIL; import dateutil" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Some dependencies may be missing
    echo.
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        echo Please run: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo [INFO] Starting Expense Tracker Pro...
echo.

REM Start the application
python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application crashed
    echo Please check the error message above
    pause
)
