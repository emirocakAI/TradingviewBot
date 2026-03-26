import os
import asyncio
import streamlit as st
from playwright.async_api import async_playwright
import requests
from io import BytesIO
import re

# --- 1. SİSTEM HAZIRLIĞI ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

# --- 2. ESKİ USUL SNAPSHOT YAKALAMA (COLAB MANTIĞI) ---
async def get_tv_snapshot(ticker, period_label, theme):
    async with async_playwright() as p:
        # Tarayıcıyı kullanıcı gibi gösteriyoruz
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Sayfaya git
        url = f"https://www.tradingview.com/symbols/BIST-{ticker}/"
        await page.goto(url, wait_until="domcontentloaded")
        
        # Grafik ve butonların yüklenmesi için güvenli bekleme
        await asyncio.sleep(8)
        
        try:
            # Dark Mode: Eğer seçiliyse sayfaya direkt karanlık tema class'ını bas
            if theme == "Dark Mod":
                await page.evaluate("document.documentElement.classList.add('theme-dark')")
                await asyncio.sleep(1)

            # Periyot Seçimi (1 Ay, 6 Ay vb.)
            period_btn = page.get_by_role("button", name=re.compile(period_label, re.IGNORECASE))
            await period_btn.click()
            await asyncio.sleep(2)

            # --- NOKTA ATIŞI: KAMERA BUTONU ---
            # Hatayı önlemek için butonun görünür olmasını bekliyoruz
            camera_selector = "[data-name='take-a-snapshot']"
            await page.wait_for_selector(camera_selector, timeout=15000)
            
            # Yeni sekme açılmasını bekleyen context
            async with page.expect_popup() as popup_info:
                await page.click(camera_selector)
            
            # Açılan yeni sekme (Snapshot URL)
            snapshot_page = popup_info.value
            await snapshot_page.wait_for_load_state("networkidle")
            
            # Bu sayfadaki saf resmi (img) çekiyoruz
            # Bu, TradingView'ın bize sunduğu en temiz, reklamsız grafiktir.
            img_element = snapshot_page.locator("img")
            img_bytes = await img_element.screenshot()
            
            await browser.close()
            return img_bytes

        except Exception as e:
            # Hata durumunda en azından ekranın grafik kısmını kurtar
            st.error(f"Snapshot alınırken hata oluştu: {e}")
            img_bytes = await page.screenshot(clip={'x': 0, 'y': 150, 'width': 1200, 'height': 600})
            await browser.close()
            return img_bytes

# --- 3. STREAMLIT ARAYÜZÜ ---
st.set_page_config(page_title="TV Snapshot Bot", layout="wide")
st.title("📈 TradingView Temiz Grafik Yakalayıcı")

with st.sidebar:
    ticker = st.text_input("Hisse Kodu (BIST):", value="THYAO").upper()
    period = st.selectbox("Periyot:", ["1 day", "5 days", "1 month", "6 months", "Year to date", "1 year", "All time"])
    theme = st.radio("Tema:", ["Beyaz Mod", "Dark Mod"])
    run_btn = st.button("🚀 Grafiği Getir")

if run_btn:
    with st.spinner("Kamera butonuna gidiliyor, temiz grafik alınıyor..."):
        try:
            image_data = asyncio.run(get_tv_snapshot(ticker, period, theme))
            
            # Sonucu ekrana bas
            st.image(image_data, caption=f"{ticker} - {period} ({theme})", use_column_width=True)
            
            # İndirme butonu
            st.download_button(
                label="📥 Grafiği Bilgisayara Kaydet",
                data=image_data,
                file_name=f"{ticker}_{period}.png",
                mime="image/png"
            )
        except Exception as e:
            st.error(f"Bir şeyler ters gitti: {e}")

st.divider()
st.info("Bu sürüm, font eklemesi yapılmamış, doğrudan 'Kamera' linkinden çekim yapan en stabil versiyondur.")
