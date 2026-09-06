@echo off
REM Modeling Stage Runner - Windows Batch

echo ========================================
echo Data Modeling Stage (Star Schema)
echo ========================================
echo.

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python run_modeling.py %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Modeling completed successfully!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Modeling failed!
    echo ========================================
)

echo.
echo Press any key to exit...
pause >nul
