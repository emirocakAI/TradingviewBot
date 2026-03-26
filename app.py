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
        # Getiri: Black 24 (Görsel doygunluk için 26 yapıldı)
        font_black = ImageFont.truetype(FONT_PATH, 26) 
        return font_semibold, font_black
    except:
        return ImageFont.load_default(), ImageFont.load_default()

# --- 2. VERİ ÇEKME VE EKRAN GÖRÜNTÜSÜ ---
async def fetch_data_and_screenshot(ticker, period_label, theme):
    async with async_playwright() as p:
        # Bot korumasını aşan ayarlar
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        
        # Tema seçimine göre zorunlu renk şeması (dark/light)
        color_scheme = "dark" if theme == "Dark Mod" else "light"
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={'width': 1200, 'height': 800},
            color_scheme=color_scheme
        )
        
        page = await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # TradingView Sembol Sayfası
        await page.goto(f"https://www.tradingview.com/symbols/BIST-{ticker}/", wait_until="domcontentloaded")
        await asyncio.sleep(6) 
        
        try:
            # Otomatik Şirket İsmi
            raw_name = await page.locator("h1").first.inner_text()
            company_name = raw_name.split("Grafiği")[0].strip()
            
            # Periyot Butonuna Tıklama ve Getiri Çekme
            period_button = page.get_by_role("button", name=re.compile(period_label, re.IGNORECASE))
            await period_button.click()
            await asyncio.sleep(1.5)
            btn_text = await period_button.inner_text()
            yield_val = re.search(r"[-+]?\d*[.,]\d+%", btn_text).group() if "%" in btn_text else "0.00%"
        except:
            company_name, yield_val = ticker, "Veri Alınamadı"

        # Ekran Görüntüsü
        path = f"{ticker}_raw.png"
        await page.screenshot(path=path)
        await browser.close()
        return path, company_name, yield_val

# --- 3. GÖRSEL İŞLEME ---
def process_image(path, company, period_label, yield_val, theme):
    img = Image.open(path)
    draw = ImageDraw.Draw(img)
    f_semi, f_black = get_styled_fonts()
    
    # Tema rengine göre yazı rengi (Beyaz modda siyah yazı, Dark modda beyaz yazı)
    text_color = "black" if theme == "Beyaz Mod" else "white"
    yield_color = "#089981" if "-" not in yield_val else "#f23645" # TV standart yeşil/kırmızı
    
    # 1. Şirket İsmi (Outfit Semibold 24)
    draw.text((50, 40), str(company).upper(), font=f_semi, fill=text_color)
    
    # 2. Tarih Aralığı ve Getiri (Outfit Black 24)
    report_line = f"{period_label} Getiri: {yield_val}"
    draw.text((50, 80), report_line, font=f_black, fill=yield_color)
    
    final_path = "finanszone_output.png"
    img.save(final_path)
    return final_path

# --- 4. KULLANICI ARAYÜZÜ (İSTEDİĞİN SORULAR) ---
st.set_page_config(page_title="FinansZone Rapor Botu", layout="centered")

st.title("📊 FinansZone Rapor Oluşturucu")
st.write("Bilgileri girin, grafiğiniz ve performans verileriniz otomatik hazırlansın.")

# Senin istediğin sorular:
ticker = st.text_input("1. Hisse Kısa Kodu (Örn: SAHOL):", value="SAHOL").upper()

period_map = {
    "1 Gün": "1 day",
    "5 Gün": "5 days",
    "1 Ay": "1 month",
    "6 Ay": "6 months",
    "YTD": "Year to date",
    "1 Yıl": "1 year",
    "5 Yıl": "5 years",
    "10 Yıl": "10 years",
    "Tümü": "All"
}
period_choice = st.selectbox("2. Tarih Aralığı Seçin:", list(period_map.keys()), index=2) # Varsayılan 1 Ay

theme_choice = st.radio("3. Tema Seçin:", ["Beyaz Mod", "Dark Mod"], horizontal=True)

if st.button("🚀 Raporu Hazırla"):
    with st.spinner(f"Lütfen bekleyin, {ticker} verileri {theme_choice} ile hazırlanıyor..."):
        try:
            # Veri ve ekran görüntüsü al
            raw_path, auto_name, auto_yield = asyncio.run(
                fetch_data_and_screenshot(ticker, period_map[period_choice], theme_choice)
            )
            
            # Görseli düzenle
            final_report = process_image(raw_path, auto_name, period_choice, auto_yield, theme_choice)
            
            # Sonucu göster
            st.success(f"Analiz Tamamlandı: {auto_name}")
            st.image(final_report)
            
            with open(final_report, "rb") as f:
                st.download_button("📥 Görseli Kaydet", f, file_name=f"FinansZone_{ticker}.png")
                
        except Exception as e:
            st.error(f"Sistem bir engelle karşılaştı: {e}")

st.divider()
st.caption("FinansZone AI Trading System - 2026")
