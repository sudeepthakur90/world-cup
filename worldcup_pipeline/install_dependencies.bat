@echo off
REM Easy Dependency Installation for Windows
REM This installs packages one by one to avoid conflicts

echo ========================================
echo Installing World Cup Pipeline Dependencies
echo ========================================
echo.

REM Navigate to project directory
cd /d "%~dp0"

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found!
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
)

echo.
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo ========================================
echo Installing Core Dependencies
echo ========================================

echo.
echo [1/8] Installing numpy...
pip install numpy

echo.
echo [2/8] Installing pandas...
pip install pandas

echo.
echo [3/8] Installing openpyxl (for Excel files)...
pip install openpyxl

echo.
echo [4/8] Installing pyarrow (for Parquet files)...
pip install pyarrow

echo.
echo [5/8] Installing requests (for downloads)...
pip install requests

echo.
echo [6/8] Installing sqlalchemy (for database)...
pip install sqlalchemy

echo.
echo [7/8] Installing python-dotenv (for config)...
pip install python-dotenv

echo.
echo [8/8] Installing psutil (for system info)...
pip install psutil

echo.
echo ========================================
echo Installation Complete!
echo ========================================

echo.
echo Testing installation...
python -c "import pandas; import numpy; import openpyxl; import requests; print('\n✓ All core packages installed successfully!')"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✓ SUCCESS!
    echo ========================================
    echo.
    echo You can now run:
    echo   python test_download.py
    echo   python run_ingestion.py
    echo   python run_adaptive_pipeline.py
) else (
    echo.
    echo ========================================
    echo ✗ Some packages failed to install
    echo ========================================
    echo.
    echo Please check the errors above.
)

echo.
echo Press any key to exit...
pause >nul
