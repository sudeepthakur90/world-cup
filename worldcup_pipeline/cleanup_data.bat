@echo off
REM Data Cleanup Utility - Windows Batch Script

echo ========================================
echo Data Cleanup Utility
echo ========================================
echo.
echo This will remove all downloaded data:
echo   - Raw data files
echo   - Processed data files
echo   - Output files
echo   - Log files
echo.
echo ========================================
echo.

set /p confirm="Are you sure? (yes/no): "

if /i "%confirm%" NEQ "yes" (
    if /i "%confirm%" NEQ "y" (
        echo.
        echo Cleanup cancelled.
        pause
        exit /b 0
    )
)

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python cleanup_data.py

echo.
echo Press any key to exit...
pause >nul
