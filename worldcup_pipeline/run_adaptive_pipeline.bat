@echo off
REM World Cup Pipeline - Easy Runner for Windows
REM Just double-click this file to run the pipeline!

echo ========================================
echo World Cup Data Pipeline
echo ========================================
echo.

REM Navigate to project directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\activate
    echo Then run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Run adaptive pipeline
echo.
echo Running adaptive pipeline...
echo.
python run_adaptive_pipeline.py %*

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Pipeline completed successfully!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Pipeline failed with error code %ERRORLEVEL%
    echo ========================================
)

echo.
echo Press any key to exit...
pause >nul