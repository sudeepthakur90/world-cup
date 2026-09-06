@echo off
REM Enrichment Stage Runner - Windows Batch

echo ========================================
echo Data Enrichment Stage
echo ========================================
echo.

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python run_enrichment.py %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Enrichment completed successfully!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Enrichment failed!
    echo ========================================
)

echo.
echo Press any key to exit...
pause >nul
