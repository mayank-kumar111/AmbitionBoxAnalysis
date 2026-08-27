@echo off
REM ---- AmbitionBox Analysis — one-click launcher (Windows) ----
cd /d "%~dp0"
echo Installing dependencies (first run only)...
python -m pip install -r requirements.txt
echo.
echo Starting AmbitionBox Analysis at http://127.0.0.1:5000
start "" http://127.0.0.1:5000
python run_with_history.py
pause
