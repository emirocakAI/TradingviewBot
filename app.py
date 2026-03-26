import streamlit as st
import asyncio
import os
import re
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

# --- 1. SİSTEM HAZIRLIĞI ---
# Bulut sunucuda Playwright'ın çalışması için kurulumu zorla
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

# --- 2. ASIL PLAYWRIGHT MANTIĞI ---
async def fetch_tradingview_report(symbol, timeframe_text, is_dark):
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
        # Bot korumasını aşmak için user_agent şart
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # 1. Sayfaya Git
        url = f"https://www.tradingview.com/symbols/BIST-{ticker}/?timeframe={selected_tf['url']}"
        await page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(7) # Grafiğin oturması için süre

        # 2. Dark Mode Ayarı (Senin o meşhur 3 tık metodu)
        if is_dark:
            try:
                await page.get_by_role("button", name="Open user menu").click()
                await asyncio.sleep(1)
                # Playwright bazen label'ı bulamazsa diye force=True
                await page.locator("label").filter(has_text="Dark theme").click(force=True)
                await page.evaluate("document.documentElement.classList.add('theme-dark')")
                await page.keyboard.press("Escape")
            except: pass

        # 3. Verileri Çek
        try:
            full_name = await page.locator("h1").first.inner_text()
            full_name = full_name.split("Grafiği")[0].strip()
            
            # Zaman periyodu butonundaki yüzdeyi yakala
            target_button = page.get_by_role("button", name=re.compile(selected_tf['query'], re.IGNORECASE))
            btn_text = await target_button.inner_text()
            return_rate = re.search(r"[-+]?\d*[.,]\d+%", btn_text).group() if "%" in btn_text else "0.00%"
        except:
            full_name, return_rate = ticker, "N/A"

        # 4. KAMERA BUTONU VE İNDİRME (Nokta Atışı)
        try:
            # Önce snapshot menüsünü aç
            await page.get_by_role("button", name="Take a snapshot").click()
            await asyncio.sleep(1)
            
            # Download image satırına tıkla ve indirilen dosyayı yakala
            async with page.expect_download() as download_info:
                await page.get_by_role("row", name="Download image").click()
            
            download = await download_info.value
            temp_path = f"temp_{ticker}.png"
            await download.save_as(temp_path)
        except Exception as e:
            # Eğer kamera butonu patlarsa (ki bazen saklanır), ekranı manuel kırp
            temp_path = f"temp_{ticker}.png"
            await page.screenshot(path=temp_path, clip={'x': 300, 'y': 200, 'width': 1200, 'height': 600})

        await browser.close()
        return temp_path, {"name": full_name, "ticker": ticker, "range": timeframe_text, "return": return_rate, "dark": is_dark}

# --- 3. GÖRSEL İŞLEME ---
def finalize_image(path, data):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    
    # Alt ve üstteki gereksiz TV boşluklarını temizle
    img = img.crop((0, 20, w, h - 40)) 
    
    header_h = 140
    bg_color = (19, 23, 34) if data['dark'] else (255, 255, 255) # TV Dark Mode Arkaplanı
    new_img = Image.new('RGB', (w, img.height + header_h), color=bg_color)
    new_img.paste(img, (0, header_h))
    
    draw = ImageDraw.Draw(new_img)
    
    # Renkler
    txt_color = (255, 255, 255) if data['dark'] else (0, 0, 0)
    is_neg = "-" in data['return'] or "−" in data['return']
    accent = (255, 82, 82) if is_neg else (38, 166, 154)

    # Not: Font dosyası klasöründe değilse default fonta düşer
    try:
        f_main = ImageFont.truetype("Outfit-VariableFont_wght.ttf", 40)
        f_sub = ImageFont.truetype("Outfit-VariableFont_wght.ttf", 25)
    except:
        f_main = f_sub = ImageFont.load_default()

    draw.text((40, 30), data['name'].upper(), fill=txt_color, font=f_main)
    draw.text((40, 85), f"{data['ticker']} • {data['range']}", fill=(130, 130, 130), font=f_sub)
    draw.text((w - 220, 45), data['return'], fill=accent, font=f_main)
    
    final_path = f"Final_{data['ticker']}.png"
    new_img.save(final_path, quality=95)
    return final_path

# --- 4. STREAMLIT UI ---
st.set_page_config(page_title="FinansZone Rapor", layout="centered")

st.title("📈 Profesyonel Grafik Raporu")
st.write("Colab Kararlılığında, TradingView Snapshot Altyapısı.")

with st.sidebar:
    st.header("⚙️ Ayarlar")
    symbol = st.text_input("Hisse Sembolü", value="THYAO")
    timeframe = st.selectbox("Zaman Aralığı", ["1 gün", "5 gün", "1 ay", "6 ay", "YTD", "1 yıl", "5 yıl", "Tümü"])
    theme = st.radio("Tema", ["Aydınlık", "Karanlık"])
    dark_mode = theme == "Karanlık"

if st.button("🚀 Raporu Oluştur"):
    with st.spinner("TradingView'dan görsel indiriliyor ve işleniyor..."):
        try:
            # Streamlit içinde asenkron fonksiyona giriş
            raw_path, info = asyncio.run(fetch_tradingview_report(symbol, timeframe, dark_mode))
            final_report = finalize_image(raw_path, info)
            
            st.success("✅ Rapor Hazır!")
            st.image(final_report)
            
            with open(final_report, "rb") as file:
                st.download_button("📥 Görseli İndir", file, f"{symbol}_Rapor.png", "image/png")
            
            # Geçici dosyaları temizle
            if os.path.exists(raw_path): os.remove(raw_path)
        except Exception as e:
            st.error(f"Hata oluştu: {e}")

st.caption("Veriler doğrudan TradingView 'Download Image' fonksiyonu ile çekilmektedir.")
