@echo off
title SignAI — AI-Powered Multilingual Sign Language System
echo ===============================================================
echo   SignAI — Starting Application Server...
echo   Open http://127.0.0.1:5000 in your browser
echo ===============================================================

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ and check 'Add Python to PATH'.
    pause
    exit /b 1
)

echo Checking dependencies...
python -c "import flask, mediapipe, cv2, sklearn, deep_translator" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages from requirements.txt...
    pip install -r requirements.txt
)

echo.
echo Launching SignAI server at http://127.0.0.1:5000
start http://127.0.0.1:5000
python app.py
pause
