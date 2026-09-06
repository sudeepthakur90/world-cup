@echo off
REM Transformation Stage Runner - Windows Batch

echo ========================================
echo Data Transformation Stage
echo ========================================
echo.

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python run_transformation.py %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Transformation completed successfully!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Transformation failed!
    echo ========================================
)

echo.
echo Press any key to exit...
pause >nul
