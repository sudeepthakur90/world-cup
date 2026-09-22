@echo off
REM AI-Readiness Validation Runner - Windows Batch

echo ========================================
echo AI-Readiness Validation
echo ========================================
echo.

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python run_ai_readiness.py %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Validation completed successfully!
    echo ========================================
    echo.
    echo Report saved to: data\output\ai_readiness_report.json
    echo.
    echo Check your AI-readiness score above.
) else (
    echo.
    echo ========================================
    echo Validation failed!
    echo ========================================
    echo.
    echo Please check the error messages above.
)

echo.
echo Press any key to exit...
pause >nul
