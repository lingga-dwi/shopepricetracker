"""Logika inti: cek harga satu/semua produk, simpan ke DB, kirim notifikasi bila perlu."""
from __future__ import annotations
import os
import time
import traceback

import db
from scraper import fetch_product_price
from notifier import send_telegram_message, format_price_alert

DELAY_BETWEEN_PRODUCTS = float(os.environ.get("DELAY_BETWEEN_PRODUCTS", "10"))


def check_one_product(product: dict) -> dict:
    """Cek harga satu produk, simpan histori, kirim notifikasi jika di bawah target.

    Returns dict berisi status hasil pengecekan.
    """
    url = product["url"]
    product_id = product["id"]
    result = {"product_id": product_id, "url": url, "ok": False, "price": None, "error": None}

    try:
        info = fetch_product_price(url)
    except Exception as e:
        result["error"] = str(e)
        traceback.print_exc()
        return result

    db.add_price_point(product_id, info.price, info.price_before_discount, info.stock)

    # Update nama produk otomatis kalau belum ada / berubah
    if not product.get("name") or product.get("name") != info.name:
        with db.get_conn() as conn:
            conn.execute("UPDATE products SET name = ? WHERE id = ?", (info.name, product_id))
            conn.commit()

    result["ok"] = True
    result["price"] = info.price
    result["name"] = info.name

    target_price = product.get("target_price")
    if target_price is not None and info.price <= target_price:
        if not db.was_notified_recently(product_id, info.price):
            sent = send_telegram_message(format_price_alert(info.name, info.price, target_price, url))
            if sent:
                db.record_notification(product_id, info.price)
                result["notified"] = True

    return result


def check_all_products(active_only: bool = True, delay: float | None = None, progress_cb=None) -> list[dict]:
    """Cek semua produk aktif satu per satu, dengan jeda antar produk."""
    delay = DELAY_BETWEEN_PRODUCTS if delay is None else delay
    products = db.get_products(active_only=active_only)
    results = []

    for i, product in enumerate(products):
        if progress_cb:
            progress_cb(i, len(products), product)

        res = check_one_product(product)
        results.append(res)

        if i < len(products) - 1:
            time.sleep(delay)

    return results
