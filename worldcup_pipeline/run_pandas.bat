@echo off
REM Force Pandas Engine

echo ========================================
echo World Cup Pipeline - Pandas Mode
echo ========================================
echo.

cd /d "%~dp0"
call venv\Scripts\activate.bat

echo Running with Pandas engine...
echo.
python run_adaptive_pipeline.py --engine pandas

echo.
echo Press any key to exit...
pause >nul