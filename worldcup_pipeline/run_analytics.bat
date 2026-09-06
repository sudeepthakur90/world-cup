@echo off
REM Analytics Stage Runner - Windows Batch

echo ========================================
echo Analytics Stage (SQL Queries)
echo ========================================
echo.

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python run_analytics.py %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Analytics completed successfully!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Analytics failed!
    echo ========================================
)

echo.
echo Press any key to exit...
pause >nul
