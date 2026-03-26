import os
import asyncio
import re
import streamlit as st
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

# --- 1. SİSTEM VE FONT AYARLARI ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

FONT_PATH = "Outfit-VariableFont_wght.ttf"

def get_styled_fonts():
    try:
        # Şirket İsmi: Semibold 24
        font_semibold = ImageFont.truetype(FONT_PATH, 24)
        # Getiri: Black 24 (Görsel ağırlık için 26 punto önerilir)
        font_black = ImageFont.truetype(FONT_PATH, 26) 
        return font_semibold, font_black
    except:
        return ImageFont.load_default(), ImageFont.load_default()

# --- 2. OTOMATİK VERİ ÇEKME VE EKRAN GÖRÜNTÜSÜ ---
async def fetch_auto_data_and_screenshot(ticker, period_label):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={'width': 1200, 'height': 800}
        )
        page = await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # TradingView Sembol Sayfasına Git
        await page.goto(f"https://www.tradingview.com/symbols/BIST-{ticker}/", wait_until="domcontentloaded")
        await asyncio.sleep(6) # Verilerin yüklenmesi için bekleme
        
        try:
            # OTOMATİK BİLGİ 1: Şirket İsmi (H1 etiketinden çekilir)
            raw_name = await page.locator("h1").first.inner_text()
            company_name = raw_name.split("Grafiği")[0].strip() # "SASA Grafiği" -> "SASA"
            
            # OTOMATİK BİLGİ 2: Getiri Oranı
            # Seçilen periyoda göre (1A, 6A, YB) butona tıkla ve değeri al
            period_button = page.get_by_role("button", name=re.compile(period_label, re.IGNORECASE))
            await period_button.click()
            await asyncio.sleep(1)
            btn_text = await period_button.inner_text()
            # Buton metni içindeki yüzdeyi ayıkla (Örn: "1A %12.45" -> "%12.45")
            yield_val = re.search(r"[-+]?\d*[.,]\d+%", btn_text).group() if "%" in btn_text else "0.00%"
            
        except Exception:
            company_name, yield_val = ticker, "Veri Alınamadı"

        # Ekran Görüntüsü Al
        path = f"{ticker}_raw.png"
        await page.screenshot(path=path)
        await browser.close()
        return path, company_name, yield_val

# --- 3. GÖRSELİ İŞLEME ---
def process_image(path, company, date_range, yield_val):
    img = Image.open(path)
    draw = ImageDraw.Draw(img)
    f_semi, f_black = get_styled_fonts()
    
    # Şirket İsmi: OUTFIT SEMIBOLD 24 PUNTO
    draw.text((50, 50), str(company).upper(), font=f_semi, fill="white")
    
    # Tarih Aralığı ve Getiri: OUTFIT BLACK 24 PUNTO
    # Getiri rengini pozitifse yeşil yapalım
    color = "#26a69a" if "-" not in yield_val else "#ef5350"
    report_line = f"{date_range} Getiri: {yield_val}"
    draw.text((50, 90), report_line, font=f_black, fill=color)
    
    final_path = "finanszone_final.png"
    img.save(final_path)
    return final_path

# --- 4. STREAMLIT ARAYÜZÜ (GÜNCELLENDİ) ---
st.set_page_config(page_title="FinansZone Otomatik Rapor", layout="centered")
st.title("🚀 FinansZone Otomatik Grafik Botu")

# Kullanıcıdan sadece Ticker ve Tarih metnini istiyoruz, gerisi otomatik.
col1, col2 = st.columns(2)
with col1:
    ticker = st.text_input("Hisse Kodu (Örn: SASA):", "SASA").upper()
    period_selection = st.selectbox("Getiri Periyodu:", ["1 month", "6 months", "Year to date", "1 year"])
with col2:
    date_range_label = st.text_input("Görseldeki Tarih (Örn: 01-26 Mart):", "01-26 Mart")

if st.button("Verileri Çek ve Raporu Hazırla"):
    with st.spinner("TradingView'dan veriler ve grafik çekiliyor..."):
        try:
            # Verileri otomatik çek
            raw_path, auto_company, auto_yield = asyncio.run(fetch_auto_data_and_screenshot(ticker, period_selection))
            
            # Görseli işle
            final_report = process_image(raw_path, auto_company, date_range_label, auto_yield)
            
            # Sonucu Göster
            st.success(f"Bulunan Şirket: {auto_company} | Getiri: {auto_yield}")
            st.image(final_report)
            
            with open(final_report, "rb") as f:
                st.download_button("📥 Görseli İndir", f, "finanszone_rapor.png")
                
        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
