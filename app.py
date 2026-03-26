import os
import asyncio
import re  # <--- Hatanın çözümü burada, bu satır eksikti.
import streamlit as st
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# --- 1. SİSTEM VE FONT AYARLARI ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

FONT_PATH = "Outfit-VariableFont_wght.ttf"

def get_styled_fonts():
    try:
        # Şirket: Semibold 24 | Getiri: Black 26
        font_semibold = ImageFont.truetype(FONT_PATH, 24)
        font_black = ImageFont.truetype(FONT_PATH, 26) 
        return font_semibold, font_black
    except:
        return ImageFont.load_default(), ImageFont.load_default()

# --- 2. 3 TIK VE KAMERA SNAPSHOT STRATEJİSİ ---
async def fetch_tradingview_snapshot(ticker, period_label, theme):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        
        # Dark Mode Emülasyonu
        color_scheme = "dark" if theme == "Dark Mod" else "light"
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            color_scheme=color_scheme
        )
        page = await context.new_page()
        
        # 1. Sayfaya Git
        await page.goto(f"https://www.tradingview.com/symbols/BIST-{ticker}/", wait_until="networkidle")
        await asyncio.sleep(5)
        
        try:
            # 2. Şirket İsmi ve Getiri Verisini Çek
            raw_name = await page.locator("h1").first.inner_text()
            company_name = raw_name.split("Grafiği")[0].strip()
            
            # Zaman aralığı butonuna tıkla
            period_button = page.get_by_role("button", name=re.compile(period_label, re.IGNORECASE))
            await period_button.click()
            await asyncio.sleep(2)
            
            btn_text = await period_button.inner_text()
            # Düzenli ifade (re) ile yüzdeyi ayıkla
            yield_val = re.search(r"[-+]?\d*[.,]\d+%", btn_text).group() if "%" in btn_text else "0.00%"
            
            # 3. DARK MODE VE TEMİZLİK (3 TIK MANTIĞI)
            if theme == "Dark Mod":
                # Sayfa elementlerine dark class'ı enjekte ederek grafik içini de karartıyoruz
                await page.evaluate("document.documentElement.classList.add('theme-dark')")
                await asyncio.sleep(1)

            # 4. KAMERA (SNAPSHOT) ODAĞI
            # Sayfadaki karmaşayı değil, sadece grafik kutusunu yakalıyoruz
            chart_area = page.locator("div[class*='chartContainer-'], .tv-category-header__price-chart").first
            img_bytes = await chart_area.screenshot()
            
        except Exception as e:
            st.warning(f"Otomatik veri çekme hatası: {e}")
            img_bytes = await page.screenshot()
            company_name, yield_val = ticker, "Veri Alınamadı"

        await browser.close()
        return img_bytes, company_name, yield_val

# --- 3. GÖRSELİ İŞLEME ---
def process_final_image(img_bytes, company, period_label, yield_val, theme):
    img = Image.open(BytesIO(img_bytes))
    draw = ImageDraw.Draw(img)
    f_semi, f_black = get_styled_fonts()
    
    # Tema ayarları
    text_color = "black" if theme == "Beyaz Mod" else "white"
    yield_color = "#089981" if "-" not in yield_val else "#f23645" # Yeşil / Kırmızı
    
    # Sol Üst Köşe Yazımı (Outfit Fontları ile)
    draw.text((40, 40), str(company).upper(), font=f_semi, fill=text_color)
    draw.text((40, 85), f"{period_label} Getiri: {yield_val}", font=f_black, fill=yield_color)
    
    output = BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()

# --- 4. STREAMLIT UI ---
st.set_page_config(page_title="FinansZone Snapshot", layout="centered")
st.title("📸 FinansZone Grafik Botu")

col1, col2 = st.columns(2)
with col1:
    ticker = st.text_input("Hisse Kodu:", "SAHOL").upper()
    theme_choice = st.radio("Tema:", ["Beyaz Mod", "Dark Mod"], horizontal=True)
with col2:
    period_choice = st.selectbox("Tarih Aralığı:", ["1 day", "5 days", "1 month", "6 months", "Year to date", "1 year", "All time"])

if st.button("🚀 Raporu Oluştur"):
    with st.spinner(f"Kamera butonu aktifleşiyor, {theme_choice} grafik hazırlanıyor..."):
        try:
            raw_img, auto_name, auto_yield = asyncio.run(
                fetch_tradingview_snapshot(ticker, period_choice, theme_choice)
            )
            final_report = process_final_image(raw_img, auto_name, period_choice, auto_yield, theme_choice)
            
            st.image(final_report)
            st.download_button("📥 Görseli Kaydet", final_report, file_name=f"{ticker}_analiz.png")
        except Exception as e:
            st.error(f"Sistem hatası: {e}")
