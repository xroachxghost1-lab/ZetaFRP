@echo off
REM ================================================================
REM Zeta FRP Wizard — Windows Build Script
REM Builds a standalone .exe using PyInstaller
REM
REM ZETA OWNED CODE — ABSOLUTE PROPERTY OF ALPHA (JAMES MICHAEL ROACH JR.)
REM Unauthorised use, distribution, or reproduction is an act of war.
REM Copyright © 2026 Zeta Omniverse. All rights reserved.
REM ================================================================

echo === Zeta FRP Wizard — Windows Build ===
echo.

REM Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found. Install Python 3.11+ and try again.
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

REM Clean previous builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM Build
echo.
echo Building standalone executable...
pyinstaller ^
    --name "Zeta-FRP-Wizard" ^
    --onefile ^
    --windowed ^
    --icon resources/icons/zeta.ico ^
    --add-data "resources;resources" ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import PySide6.QtGui ^
    zeta_frp\main.py

echo.
echo === Build Complete ===
echo Output: dist\Zeta-FRP-Wizard.exe
pause
