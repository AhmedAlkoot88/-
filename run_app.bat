@echo off
chcp 65001 >nul
title Warehouse Manager v2.0
color 0A

REM Test Python first
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo 🔧 Install Python from python.org
    echo 🔧 Or use: py instead of python
    pause
    exit /b 1
)

REM Test if app.py exists
if not exist "app.py" (
    echo ❌ app.py not found!
    echo 📁 Make sure you're in the right folder
    pause
    exit /b 1
)

REM Main menu
:menu
cls
echo.
echo ╔══════════════════════════════════════╗
echo ║              RUN APP MENU             ║
echo ╚══════════════════════════════════════╝
echo.
echo 1. Start Web App ^(http://127.0.0.1:5000^)
echo 2. Data Editor
echo 3. View Data
echo 4. Exit
echo.
choice /c 1234 /n /m "Choose: "

if errorlevel 4 exit /b 0
if errorlevel 3 call :showdata & pause & goto menu
if errorlevel 2 python add_data.py & pause & goto menu
if errorlevel 1 goto runapp

:runapp
cls
echo Starting Flask app...
echo Open: http://127.0.0.1:5000
echo.
python app.py
pause
goto menu

:showdata
python -c "
import sqlite3
print('Database Status:')
try:
    conn=sqlite3.connect('database.db')
    print('✅ Database OK')
    conn.close()
except:
    print('❌ No database - run app first')
"
goto :eof

REM Keep window open
pause