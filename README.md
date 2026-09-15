# Shopee Price Tracker

Price tracker untuk produk Shopee: ambil harga real-time lewat Chrome asli (via CDP),
simpan riwayat ke SQLite, tampilkan di dashboard Streamlit, dan kirim notifikasi Telegram
saat harga turun di bawah target.

## Cara kerja

- **scraper.py** — Playwright connect ke Chrome yang sudah berjalan (`--remote-debugging-port=9222`),
  buka halaman produk, lalu **menangkap response JSON dari endpoint `/api/v4/`** (bukan parsing HTML).
- **db.py** — penyimpanan SQLite (`data/shopeetrack.db`): tabel `products`, `price_history`, `notifications_sent`.
- **tracker.py** — orkestrasi: cek 1 atau semua produk, simpan histori, kirim notifikasi.
- **notifier.py** — kirim pesan ke Telegram Bot API.
- **scheduler.py** — jalan terus (blocking) dan cek harga semua produk otomatis pada jam-jam terjadwal
  (default `09:00,14:00,20:00`), dengan jeda antar produk (default 10 detik).
- **dashboard.py** — UI Streamlit: tambah/hapus produk, atur target harga, cek manual, grafik riwayat harga.

## Setup

1. Jalankan `setup.bat` — ini akan membuat virtual environment, install semua dependency dari
   `requirements.txt`, dan download browser Chromium untuk Playwright.
2. Salin `.env.example` menjadi `.env`, lalu isi:
   - `TELEGRAM_BOT_TOKEN` — buat bot lewat [@BotFather](https://t.me/BotFather)
   - `TELEGRAM_CHAT_ID` — dapatkan dari [@userinfobot](https://t.me/userinfobot) (chat pribadi) atau ID grup
   - `SCHEDULE_HOURS`, `DELAY_BETWEEN_PRODUCTS`, `CDP_PORT` bisa disesuaikan bila perlu.

## Menjalankan

### Dashboard (manual, interaktif)

Jalankan **`start.bat`** — ini akan:
1. Membuka Chrome dengan `--remote-debugging-port=9222` (profil terpisah di `chrome-debug-profile/`,
   supaya tidak bentrok dengan Chrome harianmu — login Shopee di jendela ini bila perlu).
2. Menjalankan dashboard Streamlit di `http://localhost:8501`.

Dari dashboard kamu bisa:
- Tambah produk lewat URL Shopee (format `https://shopee.co.id/nama-produk-i.SHOPID.ITEMID`)
- Set/ubah target harga per produk
- Cek harga satu produk (tombol 🔍) atau semua produk sekaligus
- Hapus produk (tombol 🗑️)
- Lihat grafik riwayat harga dengan garis target

### Scheduler otomatis (cek 3x sehari)

Jalankan **`start_scheduler.bat`** di jendela terpisah (biarkan tetap berjalan / bisa dijadikan
Windows Task Scheduler startup task). Scheduler akan mengecek semua produk aktif pada jam-jam
di `SCHEDULE_HOURS`, dengan jeda `DELAY_BETWEEN_PRODUCTS` detik antar produk, dan mengirim
notifikasi Telegram otomatis kalau harga ≤ target.

Untuk langsung menjalankan satu kali cek saat start (tanpa menunggu jadwal):
```
.venv\Scripts\python.exe scheduler.py --run-now
```

## Catatan penting

- Chrome **harus** dibuka lewat `--remote-debugging-port=9222` (dilakukan otomatis oleh kedua
  file `.bat`) — scraper connect ke sesi Chrome yang sedang berjalan, bukan membuka instance baru.
- Karena memakai profil Chrome terpisah (`chrome-debug-profile/`), kamu mungkin perlu login ke
  Shopee sekali di jendela tersebut agar harga anggota/promo tampil dengan benar.
- Data harga tersimpan lokal di `data/shopeetrack.db` — tidak terhapus saat aplikasi ditutup.
