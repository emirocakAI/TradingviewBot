import streamlit as st
import asyncio
import os
import re
import os

# Playwright tarayıcılarını otomatik yükle
os.system("playwright install chromium")

from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

# --- DAHA ÖNCE YAZDIĞIMIZ FONKSİYONLAR (Arka Plan) ---
async def run_playwright_logic(symbol, timeframe_text, is_dark):
    tf_map = {
        "1 gün": {"query": "1 day", "url": "1D"},
        "5 gün": {"query": "5 days", "url": "5D"},
        "1 ay": {"query": "1 month", "url": "1M"},
        "6 ay": {"query": "6 months", "url": "6M"},
        "YTD": {"query": "Year to date", "url": "YTD"},
        "1 yıl": {"query": "1 year", "url": "1Y"},
        "5 yıl": {"query": "5 years", "url": "5Y"},
        "Tümü": {"query": "All", "url": "ALL"}
    }
    selected_tf = tf_map.get(timeframe_text)
    ticker = symbol.upper().replace("BIST:", "")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            color_scheme="dark" if is_dark else "light"
        )
        page = await context.new_page()
        url = f"https://www.tradingview.com/symbols/BIST-{ticker}/?timeframe={selected_tf['url']}"
        
        await page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(10)

        # Dark Mode Zorlama (Senin bulduğun 3 tık metodu)
        if is_dark:
            try:
                await page.get_by_role("button", name="Open user menu").click()
                await asyncio.sleep(1)
                for _ in range(3):
                    await page.locator("label").filter(has_text="Dark theme").click(force=True)
                await page.evaluate("document.documentElement.classList.add('theme-dark')")
            except: pass

        # Veri Çekme
        try:
            full_name = await page.locator("h1").first.inner_text()
            full_name = full_name.split("Grafiği")[0].strip()
            target_button = page.get_by_role("button", name=re.compile(selected_tf['query'], re.IGNORECASE))
            btn_text = await target_button.inner_text()
            return_rate = btn_text.replace(selected_tf['query'], "").strip()
        except:
            full_name, return_rate = ticker, "N/A"

        # Fotoğraf Çekme
        await page.keyboard.press("Escape")
        await page.get_by_role("button", name="Take a snapshot").click(force=True)
        async with page.expect_download() as download_info:
            await page.get_by_role("row", name="Download image").click(force=True)
        
        download = await download_info.value
        path = f"temp_{ticker}.png"
        await download.save_as(path)
        await browser.close()
        return path, {"name": full_name, "ticker": ticker, "range": timeframe_text, "return": return_rate, "dark": is_dark}

# --- GÖRSEL İŞLEME ---
def finalize_image(path, data):
    img = Image.open(path)
    w, h = img.size
    img = img.crop((0, 30, w, h - 55)) # Kırpma
    
    header_h = 130
    bg_color = (31, 31, 31) if data['dark'] else (255, 255, 255)
    new_img = Image.new('RGB', (w, img.height + header_h), color=bg_color)
    new_img.paste(img, (0, header_h))
    
    draw = ImageDraw.Draw(new_img)
    # Fontlar ve Renkler (Daha önceki mantık)
    txt_color = (255, 255, 255) if data['dark'] else (0, 0, 0)
    is_neg = "-" in data['return'] or "−" in data['return']
    accent = (255, 82, 82) if is_neg else (38, 166, 154)

    draw.text((40, 30), data['name'], fill=txt_color) # Font dosyası yolu eklenmeli
    draw.text((40, 80), f"{data['ticker']} - {data['range']}", fill=(150, 150, 150))
    draw.text((w-200, 40), data['return'], fill=accent)
    
    final_path = f"Final_{data['ticker']}.png"
    new_img.save(final_path)
    return final_path

# --- STREAMLIT ARAYÜZÜ ---
st.set_page_config(page_title="BIST Rapor Oluşturucu", layout="centered")

st.title("📈 BIST Grafik Raporu Oluştur")
st.write("Hisse kısaltmasını girin ve profesyonel raporunuzu saniyeler içinde alın.")

with st.sidebar:
    st.header("⚙️ Ayarlar")
    symbol = st.text_input("Hisse Sembolü", value="SASA", help="Örn: THYAO, SAHOL")
    timeframe = st.selectbox("Zaman Aralığı", ["1 gün", "5 gün", "1 ay", "6 ay", "YTD", "1 yıl", "5 yıl", "Tümü"])
    theme = st.radio("Tema", ["Aydınlık (Beyaz)", "Karanlık (Siyah)"])
    dark_mode = theme == "Karanlık (Siyah)"

if st.button("🚀 Raporu Hazırla"):
    with st.spinner("TradingView'a bağlanılıyor ve veriler işleniyor..."):
        # Playwright asenkron çalıştığı için loop yönetimi
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            raw_path, info = loop.run_until_complete(run_playwright_logic(symbol, timeframe, dark_mode))
            final_report = finalize_image(raw_path, info)
            
            # Sonucu Göster
            st.success("✅ Rapor Hazır!")
            st.image(final_report, caption=f"{symbol} Performans Raporu")
            
            with open(final_report, "rb") as file:
                st.download_button(
                    label="📥 Görseli İndir",
                    data=file,
                    file_name=f"{symbol}_Rapor.png",
                    mime="image/png"
                )
            os.remove(raw_path) # Temizlik
        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")

st.divider()
st.caption("Veriler TradingView üzerinden otomatik çekilmektedir.")
