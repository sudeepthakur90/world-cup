@echo off
REM Force Spark Engine

echo ========================================
echo World Cup Pipeline - Spark Mode
echo ========================================
echo.

cd /d "%~dp0"
call venv\Scripts\activate.bat

echo Running with Spark engine...
echo.
python run_adaptive_pipeline.py --engine spark

echo.
echo Press any key to exit...
pause >nul