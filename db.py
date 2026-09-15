"""Lapisan database SQLite untuk Shopee Price Tracker."""
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "shopeetrack.db"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                shop_id INTEGER,
                item_id INTEGER,
                name TEXT,
                target_price REAL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                price REAL NOT NULL,
                price_before_discount REAL,
                stock INTEGER,
                checked_at TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications_sent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                price REAL NOT NULL,
                sent_at TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def add_product(url: str, shop_id: int, item_id: int, name: str, target_price: float | None):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO products (url, shop_id, item_id, name, target_price, is_active, created_at)
               VALUES (?, ?, ?, ?, ?, 1, ?)""",
            (url, shop_id, item_id, name, target_price, datetime.now().isoformat()),
        )
        conn.commit()


def remove_product(product_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()


def set_target_price(product_id: int, target_price: float | None):
    with get_conn() as conn:
        conn.execute("UPDATE products SET target_price = ? WHERE id = ?", (target_price, product_id))
        conn.commit()


def set_active(product_id: int, is_active: bool):
    with get_conn() as conn:
        conn.execute("UPDATE products SET is_active = ? WHERE id = ?", (1 if is_active else 0, product_id))
        conn.commit()


def get_products(active_only: bool = False):
    with get_conn() as conn:
        query = "SELECT * FROM products"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY created_at DESC"
        rows = conn.execute(query).fetchall()
        return [dict(r) for r in rows]


def get_product(product_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return dict(row) if row else None


def add_price_point(product_id: int, price: float, price_before_discount: float | None, stock: int | None):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO price_history (product_id, price, price_before_discount, stock, checked_at)
               VALUES (?, ?, ?, ?, ?)""",
            (product_id, price, price_before_discount, stock, datetime.now().isoformat()),
        )
        conn.commit()


def get_price_history(product_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM price_history WHERE product_id = ? ORDER BY checked_at ASC",
            (product_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_latest_price(product_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM price_history WHERE product_id = ? ORDER BY checked_at DESC LIMIT 1",
            (product_id,),
        ).fetchone()
        return dict(row) if row else None


def was_notified_recently(product_id: int, price: float) -> bool:
    """Cegah notifikasi berulang untuk harga yang sama."""
    with get_conn() as conn:
        row = conn.execute(
            """SELECT * FROM notifications_sent
               WHERE product_id = ? AND price = ?
               ORDER BY sent_at DESC LIMIT 1""",
            (product_id, price),
        ).fetchone()
        return row is not None


def record_notification(product_id: int, price: float):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO notifications_sent (product_id, price, sent_at) VALUES (?, ?, ?)",
            (product_id, price, datetime.now().isoformat()),
        )
        conn.commit()
