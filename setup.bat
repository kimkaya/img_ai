@echo off
chcp 65001 >nul
title IMG AI Studio - 설치

echo ============================================================
echo   IMG AI Studio 설치 프로그램
echo   RTX 5060 Ti 16GB 최적화
echo ============================================================
echo.

cd /d "%~dp0"

REM Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되지 않았습니다!
    echo        https://www.python.org/downloads/ 에서 Python 3.10+ 설치
    echo        설치 시 "Add Python to PATH" 체크 필수!
    pause
    exit /b 1
)

echo [1/4] Python 확인됨
python --version

echo.
echo [2/4] 가상환경 생성 (선택사항)...
REM python -m venv venv
REM call venv\Scripts\activate

echo.
echo [3/4] 설치 스크립트 실행...
python python/setup.py

echo.
echo [4/4] 설치 완료!
echo.
echo ============================================================
echo   다음 단계:
echo   1. XAMPP Apache 시작
echo   2. 브라우저: http://localhost/img_ai
echo ============================================================
echo.
pause
