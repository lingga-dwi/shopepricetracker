"""Notifikasi Telegram saat harga produk turun di bawah target."""
from __future__ import annotations
import os
import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram_message(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("[notifier] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum diset, notifikasi dilewati.")
        return False

    url = TELEGRAM_API.format(token=token)
    try:
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False},
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"[notifier] Gagal mengirim notifikasi Telegram: {e}")
        return False


def format_price_alert(name: str, price: float, target_price: float, url: str) -> str:
    return (
        f"🔔 <b>Harga Turun!</b>\n\n"
        f"📦 {name}\n"
        f"💰 Harga sekarang: <b>Rp{price:,.0f}</b>\n"
        f"🎯 Target: Rp{target_price:,.0f}\n\n"
        f"🔗 {url}"
    ).replace(",", ".")
