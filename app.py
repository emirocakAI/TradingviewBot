import os
import asyncio
import streamlit as st
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

# --- 1. SİSTEM AYARLARI ---
# Tarayıcıyı kur (Eğer yoksa)
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

FONT_PATH = "Outfit-VariableFont_wght.ttf"

def get_styled_fonts():
    try:
        # Şirket İsmi: Outfit Semibold (24)
        font_semibold = ImageFont.truetype(FONT_PATH, 24)
        # Getiri: Outfit Black (24) -> Black etkisi için puntoyu 26 yapıyoruz
        font_black = ImageFont.truetype(FONT_PATH, 26) 
        return font_semibold, font_black
    except:
        return ImageFont.load_default(), ImageFont.load_default()

# --- 2. GRAFİK YAKALAMA (Kütüphanesiz Stealth) ---
async def capture_chart(ticker):
    async with async_playwright() as p:
        # Bot engeline takılmamak için kullanıcı gibi davranan argümanlar
        browser = await p.chromium.launch(headless=True, args=[
            "--no-sandbox", 
            "--disable-blink-features=AutomationControlled"
        ])
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={'width': 1200, 'height': 800}
        )
        
        page = await context.new_page()
        
        # Manuel Stealth: Webdriver parametresini siliyoruz
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # TradingView'a git
        await page.goto(f"https://www.tradingview.com/symbols/BIST-{ticker}/", wait_until="domcontentloaded")
        
        # Sayfanın yüklenmesi için güvenli bekleme
        await asyncio.sleep(7)
        
        path = f"{ticker}.png"
        await page.screenshot(path=path)
        await browser.close()
        return path

# --- 3. GÖRSEL İŞLEME ---
def process_image(path, company, date_range, yield_val):
    img = Image.open(path)
    draw = ImageDraw.Draw(img)
    f_semi, f_black = get_styled_fonts()
    
    # Yazı Renkleri ve Pozisyonları
    # 1. Şirket İsmi (Outfit Semibold 24)
    draw.text((50, 50), str(company).upper(), font=f_semi, fill="white")
    
    # 2. Getiri (Outfit Black 24)
    draw.text((50, 90), f"{date_range} Getiri: %{yield_val}", font=f_black, fill="#00FF00")
    
    final_path = f"final_output.png"
    img.save(final_path)
    return final_path

# --- 4. STREAMLIT ARAYÜZÜ ---
st.set_page_config(page_title="FinansZone Rapor", layout="centered")
st.title("📊 FinansZone Grafik Oluşturucu")

ticker = st.text_input("Hisse Kodu (Örn: THYAO):", "THYAO").upper()
company = st.text_input("Şirket İsmi:", "TURK HAVA YOLLARI")
date_range = st.text_input("Tarih Aralığı (Örn: 01-26 Mart):", "01-26 Mart")
yield_val = st.text_input("Getiri Oranı (Örn: 15,40):", "15,40")

if st.button("Grafiği Hazırla"):
    with st.spinner("Veriler işleniyor..."):
        try:
            raw_path = asyncio.run(capture_chart(ticker))
            final_report = process_image(raw_path, company, date_range, yield_val)
            
            st.image(final_report, caption=f"{company} Performans Analizi")
            
            with open(final_report, "rb") as file:
                st.download_button("Görseli İndir", file, "finanszone_rapor.png", "image/png")
                
        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
