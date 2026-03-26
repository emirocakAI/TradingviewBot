import streamlit as st
import os
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from PIL import Image, ImageDraw, ImageFont

# --- 1. SİSTEM KURULUMU (Playwright Tarayıcı Yükleyici) ---
# Streamlit Cloud üzerinde tarayıcının yerinde olduğundan emin olur
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

# --- 2. FONT VE GÖRSEL AYARLARI ---
FONT_PATH = "Outfit-VariableFont_wght.ttf"

def get_fonts(size_company=24, size_yield=24):
    try:
        # Şirket ismi için Semibold (Pillow'da aynı dosyadan punto ile ayrılır)
        company_f = ImageFont.truetype(FONT_PATH, size_company)
        # Getiri için Black (Eğer yeterince kalın olmazsa puntoyu +1 veya +2 yapabilirsin)
        yield_f = ImageFont.truetype(FONT_PATH, size_yield)
        return company_f, yield_f
    except Exception as e:
        st.error(f"Font yükleme hatası: {e}")
        return ImageFont.load_default(), ImageFont.load_default()

# --- 3. GRAFİK YAKALAMA (PLAYWRIGHT) ---
async def capture_chart(symbol):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        await stealth_async(page)
        
        # Örnek TradingView URL'si (Kendi URL yapına göre güncelle)
        url = f"https://www.tradingview.com/chart/?symbol={symbol}"
        await page.goto(url, wait_until="networkidle")
        
        # Grafiğin yüklenmesi için kısa bir bekleme
        await asyncio.sleep(5)
        
        screenshot_path = f"{symbol}_chart.png"
        await page.screenshot(path=screenshot_path)
        await browser.close()
        return screenshot_path

# --- 4. GÖRSEL ÜZERİNE YAZI YAZMA ---
def process_image(img_path, company_name, date_range, yield_val):
    img = Image.open(img_path)
    draw = ImageDraw.Draw(img)
    
    font_company, font_yield = get_fonts(24, 24)
    
    # Koordinatlar (Temsilidir, şablonuna göre değiştir)
    # Şirket İsmi: Outfit Semibold 24
    draw.text((40, 40), company_name, font=font_company, fill="white")
    
    # Tarih Aralığı ve Getiri: Outfit Black 24
    text_yield = f"{date_range} Getiri: {yield_val}%"
    draw.text((40, 80), text_yield, font=font_yield, fill="#00FF00") # Yeşil renk örnek
    
    final_path = f"final_{company_name}.png"
    img.save(final_path)
    return final_path

# --- 5. STREAMLIT ARAYÜZÜ ---
def main():
    st.title("BIST Grafik & Getiri Raporlayıcı")
    
    col1, col2 = st.columns(2)
    with col1:
        symbol = st.text_input("Hisse Kodu (Örn: THYAO):", "THYAO")
        company_name = st.text_input("Şirket Tam İsmi:", "Türk Hava Yolları")
    with col2:
        date_range = st.text_input("Tarih Aralığı:", "01-07 Mart")
        yield_val = st.text_input("Getiri Oranı (%):", "12,45")

    if st.button("Rapor Oluştur"):
        with st.spinner("Grafik hazırlanıyor..."):
            try:
                # Grafik yakala
                raw_img = asyncio.run(capture_chart(symbol))
                # Üzerine yazı yaz
                final_img = process_image(raw_img, company_name, date_range, yield_val)
                
                # Göster ve İndir
                st.image(final_img, caption=f"{company_name} Analizi")
                with open(final_img, "rb") as file:
                    st.download_button("Görseli İndir", file, "rapor.png", "image/png")
            except Exception as e:
                st.error(f"İşlem sırasında hata: {e}")

if __name__ == "__main__":
    main()
