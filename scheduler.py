"""Scheduler otomatis: cek harga semua produk pada jam-jam terjadwal (default 3x sehari)."""
from __future__ import annotations
import os
import sys
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

load_dotenv()

import db
from tracker import check_all_products

SCHEDULE_HOURS = [h.strip() for h in os.environ.get("SCHEDULE_HOURS", "09:00,14:00,20:00").split(",") if h.strip()]


def run_check_job():
    print(f"\n{'='*60}")
    print(f"[scheduler] Mulai cek harga - {datetime.now().isoformat()}")
    print(f"{'='*60}")

    def progress(i, total, product):
        print(f"[scheduler] ({i+1}/{total}) Mengecek: {product['url']}")

    results = check_all_products(active_only=True, progress_cb=progress)

    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count
    notified = sum(1 for r in results if r.get("notified"))

    print(f"[scheduler] Selesai. Sukses: {ok_count}, Gagal: {fail_count}, Notifikasi terkirim: {notified}")
    for r in results:
        if not r["ok"]:
            print(f"[scheduler]   GAGAL {r['url']}: {r['error']}")


def main():
    db.init_db()
    print("[scheduler] Shopee Price Tracker - Scheduler dimulai")
    print(f"[scheduler] Jadwal cek harian: {', '.join(SCHEDULE_HOURS)}")
    print("[scheduler] Tekan Ctrl+C untuk berhenti.\n")

    scheduler = BlockingScheduler(timezone="Asia/Jakarta")

    for hhmm in SCHEDULE_HOURS:
        try:
            hour, minute = hhmm.split(":")
            scheduler.add_job(
                run_check_job,
                CronTrigger(hour=int(hour), minute=int(minute)),
                id=f"check_{hhmm}",
                misfire_grace_time=3600,
            )
        except ValueError:
            print(f"[scheduler] Format jam tidak valid, dilewati: {hhmm}")

    if "--run-now" in sys.argv:
        print("[scheduler] --run-now terdeteksi, menjalankan pengecekan segera...")
        run_check_job()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n[scheduler] Dihentikan oleh pengguna.")


if __name__ == "__main__":
    main()
