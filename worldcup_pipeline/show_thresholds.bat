@echo off
REM Show Engine Selection Thresholds

cd /d "%~dp0"
call venv\Scripts\activate.bat

python run_adaptive_pipeline.py --show-thresholds

echo.
echo Press any key to exit...
pause >nul