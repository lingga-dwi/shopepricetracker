@echo off
setlocal enabledelayedexpansion
title Shopee Price Tracker - Launcher
cd /d "%~dp0"
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"

echo ============================================================
echo   Shopee Price Tracker - Starting
echo ============================================================
echo.

REM --- Cari Chrome ---
set "CHROME_EXE="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"

if "%CHROME_EXE%"=="" (
    echo [ERROR] chrome.exe tidak ditemukan di lokasi standar.
    echo Edit start.bat dan set CHROME_EXE secara manual.
    pause
    exit /b 1
)

set "CDP_PORT=9222"
set "CHROME_DEBUG_PROFILE=%~dp0chrome-debug-profile"

echo [1/2] Menjalankan Chrome dengan remote debugging port %CDP_PORT% ...
start "" "%CHROME_EXE%" --remote-debugging-port=%CDP_PORT% --user-data-dir="%CHROME_DEBUG_PROFILE%" "https://shopee.co.id"

echo     Menunggu Chrome siap...
timeout /t 5 /nobreak >nul

echo [2/2] Menjalankan Dashboard Streamlit ...
echo.
echo ============================================================
echo   Dashboard akan terbuka di browser: http://localhost:8501
echo   Chrome (CDP) berjalan di port: %CDP_PORT%
echo   Tutup jendela ini untuk menghentikan dashboard.
echo ============================================================
echo.

if exist ".venv\Scripts\streamlit.exe" (
    ".venv\Scripts\streamlit.exe" run dashboard.py
) else (
    streamlit run dashboard.py
)

pause
