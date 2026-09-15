"""
Scraper harga Shopee via Playwright yang connect ke Chrome nyata lewat CDP.
Tidak parsing HTML sama sekali — mengambil response JSON dari endpoint /api/v4/.
"""
from __future__ import annotations
import os
import re
import time
from dataclasses import dataclass

from playwright.sync_api import sync_playwright, Page, Response

CDP_PORT = int(os.environ.get("CDP_PORT", "9222"))
CDP_URL = f"http://localhost:{CDP_PORT}"

# Endpoint v4 yang mengandung detail item (harga, stok, dll)
PDP_API_PATTERN = re.compile(r"/api/v4/(pdp/get_pc|item/get)")


@dataclass
class ProductPrice:
    shop_id: int
    item_id: int
    name: str
    price: float
    price_before_discount: float | None
    stock: int | None
    currency: str = "IDR"


def parse_shopee_url(url: str) -> tuple[int, int]:
    """Ekstrak shop_id dan item_id dari URL produk Shopee.

    Mendukung format:
    - https://shopee.co.id/nama-produk-i.SHOPID.ITEMID
    - https://shopee.co.id/product/SHOPID/ITEMID
    """
    m = re.search(r"-i\.(\d+)\.(\d+)", url)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"/product/(\d+)/(\d+)", url)
    if m:
        return int(m.group(1)), int(m.group(2))
    raise ValueError(f"Tidak bisa mengekstrak shop_id/item_id dari URL: {url}")


def _extract_item_json(payload: dict) -> dict | None:
    """Normalisasi berbagai bentuk response v4 menjadi dict item."""
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if isinstance(data, dict):
        if "item" in data and isinstance(data["item"], dict):
            return data["item"]
        if "price" in data or "item_id" in data:
            return data
    return None


def fetch_product_price(url: str, timeout_ms: int = 20000) -> ProductPrice:
    """Buka URL produk di tab baru Chrome (via CDP) dan tangkap response JSON /api/v4/.

    Chrome asli harus sudah berjalan dengan:
        chrome.exe --remote-debugging-port=9222
    """
    shop_id, item_id = parse_shopee_url(url)
    captured: dict = {}

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()

        def on_response(response: Response):
            if PDP_API_PATTERN.search(response.url):
                try:
                    body = response.json()
                except Exception:
                    return
                item = _extract_item_json(body)
                if item and "price" in item:
                    captured["item"] = item

        page.on("response", on_response)

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            deadline = time.time() + (timeout_ms / 1000)
            while time.time() < deadline and "item" not in captured:
                page.wait_for_timeout(300)
        finally:
            page.remove_listener("response", on_response)
            page.close()

    if "item" not in captured:
        raise RuntimeError(
            f"Gagal menangkap response /api/v4/ untuk item {item_id}. "
            "Pastikan Chrome berjalan dengan --remote-debugging-port dan sudah login jika perlu."
        )

    item = captured["item"]
    raw_price = item.get("price")
    raw_price_before = item.get("price_before_discount")

    # Harga Shopee dari API v4 dalam satuan micro (dikali 100000)
    price = raw_price / 100000 if raw_price is not None else None
    price_before = raw_price_before / 100000 if raw_price_before else None

    name = item.get("name") or item.get("title") or f"Item {item_id}"
    stock = item.get("stock")

    if price is None:
        raise RuntimeError(f"Field 'price' tidak ditemukan pada response item {item_id}")

    return ProductPrice(
        shop_id=shop_id,
        item_id=item_id,
        name=name,
        price=price,
        price_before_discount=price_before,
        stock=stock,
    )
