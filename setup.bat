@echo off
setlocal
title Shopee Price Tracker - Setup
cd /d "%~dp0"

echo ============================================================
echo   Shopee Price Tracker - Setup
echo ============================================================
echo.

echo [1/3] Membuat virtual environment (.venv) ...
py -3.13 -m venv .venv 2>nul
if errorlevel 1 (
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"

echo [2/3] Menginstal dependency Python ...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [3/3] Menginstal browser Playwright (Chromium) ...
python -m playwright install chromium

echo.
echo ============================================================
echo   Setup selesai!
echo   Salin .env.example menjadi .env lalu isi TELEGRAM_BOT_TOKEN
echo   dan TELEGRAM_CHAT_ID sebelum menjalankan start.bat
echo ============================================================
pause
