@echo off
setlocal enabledelayedexpansion
title Shopee Price Tracker - Scheduler
cd /d "%~dp0"
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"

echo ============================================================
echo   Shopee Price Tracker - Scheduler (cek otomatis 3x sehari)
echo ============================================================
echo.
echo [PENTING] Pastikan Chrome dengan --remote-debugging-port=9222
echo sudah berjalan (jalankan start.bat terlebih dahulu jika belum).
echo.

set "CHROME_EXE="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"

set "CHROME_DEBUG_PROFILE=%~dp0chrome-debug-profile"

netstat -ano | findstr :9222 >nul
if errorlevel 1 (
    echo Chrome debug belum terdeteksi di port 9222, menjalankan sekarang...
    start "" "%CHROME_EXE%" --remote-debugging-port=9222 --user-data-dir="%CHROME_DEBUG_PROFILE%" "https://shopee.co.id"
    timeout /t 5 /nobreak >nul
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" scheduler.py
) else (
    python scheduler.py
)

pause
