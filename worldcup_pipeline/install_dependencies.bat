@echo off
REM Easy Dependency Installation for Windows
REM Installs all packages from requirements.txt

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
echo Installing from requirements.txt
echo ========================================
echo.

if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo ERROR: requirements.txt not found!
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

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
