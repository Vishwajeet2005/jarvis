@echo off
title J.A.R.V.I.S. Agent
color 0B
cd /d "%~dp0"

if not exist .env (
    echo.
    echo  ERROR: .env not found.
    echo  Copy .env.example to .env and fill in your Railway URL and secret.
    echo.
    pause & exit /b 1
)

if not exist venv\Scripts\python.exe (
    echo  Setting up environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt -q
) else (
    call venv\Scripts\activate.bat
)

echo.
echo  Starting J.A.R.V.I.S. Agent...
echo  Keep this window open while using JARVIS.
echo.
python agent.py
pause
