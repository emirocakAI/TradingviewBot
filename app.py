import os
import subprocess
import sys
import asyncio
import re

# --- 1. OTOMATİK KÜTÜPHANE KONTROLÜ (Hata Almamak İçin) ---
def install_dependencies():
    try:
        from playwright_stealth import stealth_async
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright-stealth"])

install_dependencies()

import streamlit as st
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from PIL import Image, ImageDraw, ImageFont

# --- 2. SİSTEM VE FONT AYARLARI ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

FONT_PATH = "Outfit-VariableFont_wght.ttf"

def get_styled_fonts():
    try:
        # Şirket İsmi: Semibold (Punto: 24)
        # Not: Pillow'da 'semibold' etkisi için standart yükleme yapılır
        font_semibold = ImageFont.truetype(FONT_PATH, 24)
        
        # Getiri Kısmı: Black (Punto: 24)
        # Black etkisini artırmak için puntoyu 25 yapabiliriz
        font_black = ImageFont.truetype(FONT_PATH, 25) 
        
        return font_semibold, font_black
    except Exception as e:
        st.error(f"Font dosyası bulunamadı: {e}")
        return ImageFont.load_default(), ImageFont.load_default()

# --- 3. VERİ VE EKRAN GÖRÜNTÜSÜ YAKALAMA ---
async def get_tradingview_data(ticker, timeframe_query):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        await stealth_async(page)
        
        url = f"https://www.tradingview.com/symbols/BIST-{ticker}/"
        await page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(5) # Sayfanın oturması için bekleme

        try:
            # Şirket ismini çek
            full_name = await page.locator("h1").first.inner_text()
            full_name = full_name.split("Grafiği")[0].strip()

            # Getiri oranını çek
            target_button = page.get_by_role("button", name=re.compile(timeframe_query, re.IGNORECASE))
            btn_text = await target_button.inner_text()
            return_rate = btn_text.replace(timeframe_query, "").strip()
        except:
            full_name, return_rate = ticker, "0.00%"

        # Ekran görüntüsü al
        screenshot_path = f"temp_{ticker}.png"
        await page.screenshot(path=screenshot_path)
        await browser.close()
        return screenshot_path, full_name, return_rate

# --- 4. GÖRSELİ İŞLEME VE YAZILARI EKLEME ---
def create_final_report(img_path, company_name, date_range, return_val):
    img = Image.open(img_path)
    # Tasarım gereği alt/üst boşlukları kırpmak istersen burayı kullanabilirsin
    # img = img.crop((0, 50, img.width, img.height - 50))
    
    draw = ImageDraw.Draw(img)
    font_semibold, font_black = get_styled_fonts()

    # YAZI 1: Şirket İsmi (Outfit Semibold 24)
    # Koordinat (40, 40) - Beyaz renk
    draw.text((40, 40), company_name.upper(), font=font_semibold, fill="white")

    # YAZI 2: Tarih Aralığı ve Getiri (Outfit Black 24)
    # Koordinat (40, 80) - Getiri pozitifse yeşil, negatifse kırmızı yapılabilir
    color = "#26a69a" if "-" not in return_val else "#ef5350"
    report_text = f"{date_range} Getiri: {return_val}"
    draw.text((40, 80), report_text, font=font_black, fill=color)

    final_path = f"Final_Rapor_{company_name}.png"
    img.save(final_path)
    return final_path

# --- 5. STREAMLIT ARAYÜZÜ ---
st.set_page_config(page_title="FinansZone Grafik Botu", layout="centered")

st.title("📈 BIST Grafik & Performans Raporu")
st.markdown("Hisse kodunu girin, sistem otomatik olarak TradingView'dan verileri çekip raporu hazırlasın.")

with st.sidebar:
    st.header("⚙️ Parametreler")
    ticker = st.text_input("Hisse Kodu (Örn: SASA):", value="SASA").upper()
    timeframe_label = st.selectbox("Zaman Aralığı:", ["1 Ay", "6 Ay", "Yıl Başından Beri", "1 Yıl"])
    date_range_text = st.text_input("Görselde Yazacak Tarih (Örn: 01-26 Mart):", "01-26 Mart")
    
    tf_map = {
        "1 Ay": "1 month",
        "6 Ay": "6 months",
        "Yıl Başından Beri": "Year to date",
        "1 Yıl": "1 year"
    }

if st.button("🚀 Raporu Oluştur ve İndir"):
    with st.spinner("Veriler çekiliyor, lütfen bekleyin..."):
        try:
            # 1. Veri ve Görsel Çek
            raw_img, full_name, return_rate = asyncio.run(get_tradingview_data(ticker, tf_map[timeframe_label]))
            
            # 2. Görseli İşle
            final_report = create_final_report(raw_img, full_name, date_range_text, return_rate)
            
            # 3. Sonucu Göster
            st.success(f"✅ {full_name} raporu hazır!")
            st.image(final_report)
            
            with open(final_report, "rb") as f:
                st.download_button("📥 Görseli Kaydet", f, file_name=f"{ticker}_Performans.png")
                
            # Geçici dosyaları temizle
            if os.path.exists(raw_img): os.remove(raw_img)
        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")

st.divider()
st.caption("Powered by FinansZone AI - 2026")
