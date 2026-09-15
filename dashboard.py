"""Dashboard Streamlit untuk Shopee Price Tracker."""
from __future__ import annotations
import os
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import db
from scraper import parse_shopee_url
from tracker import check_one_product, check_all_products

st.set_page_config(page_title="Shopee Price Tracker", page_icon="🛒", layout="wide")

db.init_db()

st.title("🛒 Shopee Price Tracker")
st.caption("Ambil harga real-time via Chrome (CDP) + notifikasi Telegram saat harga turun")

# ---------------------------------------------------------------------------
# Sidebar: tambah produk baru
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("➕ Tambah Produk")
    with st.form("add_product_form", clear_on_submit=True):
        new_url = st.text_input("URL Produk Shopee", placeholder="https://shopee.co.id/produk-i.123.456")
        new_target = st.number_input("Target Harga (Rp)", min_value=0, step=1000, value=0)
        submitted = st.form_submit_button("Tambah", use_container_width=True)

        if submitted:
            if not new_url.strip():
                st.error("URL tidak boleh kosong.")
            else:
                try:
                    shop_id, item_id = parse_shopee_url(new_url.strip())
                    target = float(new_target) if new_target > 0 else None
                    db.add_product(new_url.strip(), shop_id, item_id, None, target)
                    st.success("Produk ditambahkan. Klik 'Cek Semua Harga' untuk ambil data pertama.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    if "UNIQUE constraint" in str(e):
                        st.error("Produk dengan URL ini sudah ada di daftar.")
                    else:
                        st.error(f"Gagal menambah produk: {e}")

    st.divider()
    st.header("⚙️ Pengaturan")
    st.text(f"CDP Port: {os.environ.get('CDP_PORT', '9222')}")
    st.text(f"Jeda antar produk: {os.environ.get('DELAY_BETWEEN_PRODUCTS', '10')}s")
    st.text(f"Jadwal: {os.environ.get('SCHEDULE_HOURS', '09:00,14:00,20:00')}")
    telegram_ok = bool(os.environ.get("TELEGRAM_BOT_TOKEN")) and bool(os.environ.get("TELEGRAM_CHAT_ID"))
    st.text(f"Telegram: {'✅ terkonfigurasi' if telegram_ok else '❌ belum diset (lihat .env)'}")

# ---------------------------------------------------------------------------
# Aksi cek harga
# ---------------------------------------------------------------------------
col1, col2 = st.columns([1, 4])
with col1:
    check_all_btn = st.button("🔄 Cek Semua Harga", type="primary", use_container_width=True)

if check_all_btn:
    products = db.get_products(active_only=True)
    if not products:
        st.warning("Belum ada produk aktif.")
    else:
        progress_bar = st.progress(0, text="Memulai pengecekan...")
        status_box = st.empty()

        def progress_cb(i, total, product):
            progress_bar.progress(i / total, text=f"Mengecek {i+1}/{total}: {product['url']}")

        results = check_all_products(active_only=True, progress_cb=progress_cb)
        progress_bar.progress(1.0, text="Selesai")

        ok = sum(1 for r in results if r["ok"])
        fail = len(results) - ok
        status_box.info(f"Selesai: {ok} berhasil, {fail} gagal.")
        for r in results:
            st.session_state.pop(f"last_error_{r['product_id']}", None)
            if not r["ok"]:
                st.session_state[f"last_error_{r['product_id']}"] = r["error"]
        st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Daftar produk
# ---------------------------------------------------------------------------
products = db.get_products()

if not products:
    st.info("Belum ada produk. Tambahkan lewat sidebar di kiri.")
else:
    for product in products:
        latest = db.get_latest_price(product["id"])
        history = db.get_price_history(product["id"])

        name = product["name"] or f"Item {product['item_id']}"
        with st.container(border=True):
            top_col1, top_col2, top_col3, top_col4 = st.columns([3, 1, 1, 1])

            with top_col1:
                st.markdown(f"**{name}**")
                st.caption(product["url"])

            with top_col2:
                if latest:
                    st.metric("Harga Terakhir", f"Rp{latest['price']:,.0f}".replace(",", "."))
                else:
                    st.metric("Harga Terakhir", "belum dicek")
                if st.session_state.get(f"last_error_{product['id']}"):
                    st.error(st.session_state[f"last_error_{product['id']}"], icon="⚠️")

            with top_col3:
                current_target = product["target_price"] or 0
                new_target = st.number_input(
                    "Target (Rp)",
                    min_value=0,
                    step=1000,
                    value=int(current_target),
                    key=f"target_{product['id']}",
                )
                if new_target != current_target:
                    db.set_target_price(product["id"], float(new_target) if new_target > 0 else None)
                    st.rerun()

            with top_col4:
                st.write("")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🔍", key=f"check_{product['id']}", help="Cek harga sekarang"):
                        with st.spinner("Mengecek harga..."):
                            res = check_one_product(product)
                        if res["ok"]:
                            st.session_state.pop(f"last_error_{product['id']}", None)
                            st.toast(f"Harga: Rp{res['price']:,.0f}".replace(",", "."))
                        else:
                            st.session_state[f"last_error_{product['id']}"] = res["error"]
                        st.rerun()
                with c2:
                    if st.button("🗑️", key=f"delete_{product['id']}", help="Hapus produk"):
                        db.remove_product(product["id"])
                        st.rerun()

            if history:
                df = pd.DataFrame(history)
                df["checked_at"] = pd.to_datetime(df["checked_at"])

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df["checked_at"], y=df["price"],
                    mode="lines+markers", name="Harga",
                    line=dict(color="#ee4d2d", width=2),
                    marker=dict(size=8),
                ))
                if product["target_price"]:
                    fig.add_hline(
                        y=product["target_price"], line_dash="dash", line_color="green",
                        annotation_text="Target",
                    )
                # Beri rentang waktu wajar di sumbu X supaya tidak zoom aneh saat titik data sedikit
                span = df["checked_at"].max() - df["checked_at"].min()
                pad = max(span * 0.1, pd.Timedelta(hours=12))
                fig.update_layout(
                    height=250, margin=dict(l=10, r=10, t=10, b=10),
                    yaxis_title="Harga (Rp)", xaxis_title=None,
                    xaxis_range=[df["checked_at"].min() - pad, df["checked_at"].max() + pad],
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{product['id']}")
                if len(history) == 1:
                    st.caption(
                        f"Baru 1 data ({df['checked_at'].iloc[0].strftime('%d %b %Y %H:%M')}). "
                        "Titik akan bertambah otomatis tiap kali scheduler jalan atau kamu klik 🔍."
                    )
            else:
                st.caption("Belum ada riwayat harga. Klik 🔍 atau 'Cek Semua Harga'.")

st.divider()
st.caption(f"Shopee Price Tracker · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
