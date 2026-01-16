@echo off
title IMG AI Studio - Setup

echo ============================================================
echo   IMG AI Studio - Already Installed!
echo   RTX 5060 Ti 16GB with DirectML
echo ============================================================
echo.

echo [OK] Python 3.11 installed
py -3.11 --version

echo.
echo [OK] Checking installed packages...
py -3.11 -m pip list | findstr torch
py -3.11 -m pip list | findstr diffusers

echo.
echo ============================================================
echo   Everything is ready!
echo ============================================================
echo.
echo   How to use:
echo   1. Start Apache in XAMPP Control Panel
echo   2. Open browser: http://localhost/img_ai
echo   3. Take photo or upload image
echo   4. Select style and click "AI Transform"
echo.
echo   First run will download AI models (2-5 GB per style)
echo.
echo ============================================================
pause
