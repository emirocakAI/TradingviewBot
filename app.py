import os
import asyncio
import streamlit as st
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# --- 1. AYARLAR VE FONT YÜKLEME ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

FONT_PATH = "Outfit-VariableFont_wght.ttf"

def get_styled_fonts():
    try:
        # Şirket: Semibold 24 | Getiri: Black 26 (Dolgunluk için)
        return ImageFont.truetype(FONT_PATH, 24), ImageFont.truetype(FONT_PATH, 26)
    except:
        return ImageFont.load_default(), ImageFont.load_default()

# --- 2. 3 TIK STRATEJİSİ VE SNAPSHOT ---
async def get_tv_snapshot(ticker, period_label, theme):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Dark mode için emülasyon
        color_scheme = "dark" if theme == "Dark Mod" else "light"
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080}, color_scheme=color_scheme)
        page = await context.new_page()
        
        # 1. Sayfaya Git
        await page.goto(f"https://www.tradingview.com/symbols/BIST-{ticker}/", wait_until="networkidle")
        await asyncio.sleep(4)
        
        try:
            # 2. Periyot Seçimi (Örn: 1 Ay)
            await page.get_by_role("button", name=period_label, exact=False).click()
            await asyncio.sleep(2)
            
            # Verileri kazı (Scraping)
            company_name = (await page.locator("h1").first.inner_text()).split("Grafiği")[0].strip()
            btn_text = await page.get_by_role("button", name=period_label, exact=False).inner_text()
            yield_val = "".join(re.findall(r"[-+]?\d*[.,]\d+%", btn_text)) or "%0.00"

            # --- 3 TIK STRATEJİSİ (DARK MODE ZORLAMA) ---
            if theme == "Dark Mod":
                # Bazı sayfalarda direkt buton varken, bazılarında menü içindedir
                # En garanti yol: Sayfa body'sine dark class'ı enjekte etmek veya temayı tetiklemek
                await page.evaluate("document.documentElement.classList.add('theme-dark')")
                await asyncio.sleep(1)

            # --- KAMERA BUTONU STRATEJİSİ ---
            # TradingView mini chart üzerindeki kamera ikonunu bul ve tıkla
            snapshot_btn = page.locator("[data-name='take-a-snapshot']").first
            await snapshot_btn.scroll_into_view_if_needed()
            
            # Direkt elementin ekran görüntüsünü almak en temizidir (Kamera çıktısı ile aynıdır)
            chart_element = page.locator("div[class*='chartContainer-'], .tv-category-header__price-chart").first
            img_bytes = await chart_element.screenshot()
            
        except Exception as e:
            st.error(f"Grafik yakalanamadı: {e}")
            img_bytes = await page.screenshot()
            company_name, yield_val = ticker, "Veri Yok"

        await browser.close()
        return img_bytes, company_name, yield_val

# --- 3. GÖRSEL İŞLEME VE FONT BASMA ---
def finalize_image(img_bytes, company, period, yield_val, theme):
    img = Image.open(BytesIO(img_bytes))
    draw = ImageDraw.Draw(img)
    f_semi, f_black = get_styled_fonts()
    
    text_color = "black" if theme == "Beyaz Mod" else "white"
    yield_color = "#089981" if "-" not in yield_val else "#f23645"
    
    # Yazıları yerleştir (Sol Üst Köşe)
    draw.text((35, 30), company.upper(), font=f_semi, fill=text_color)
    draw.text((35, 75), f"{period} Getiri: {yield_val}", font=f_black, fill=yield_color)
    
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- 4. STREAMLIT ARAYÜZÜ ---
st.set_page_config(page_title="FinansZone Snapshot", layout="centered")
st.title("📸 FinansZone Grafik Snapshot")

ticker = st.text_input("Hisse Kodu:", value="SAHOL").upper()
period = st.selectbox("Zaman Aralığı:", ["1 day", "5 days", "1 month", "6 months", "Year to date", "1 year", "All time"])
theme = st.radio("Tema Seçimi:", ["Beyaz Mod", "Dark Mod"], horizontal=True)

if st.button("🚀 Grafiği Oluştur"):
    with st.spinner("Kamera butonuna gidiliyor ve Snapshot alınıyor..."):
        img_raw, name, y_val = asyncio.run(get_tv_snapshot(ticker, period, theme))
        final_img = finalize_image(img_raw, name, period, y_val, theme)
        
        st.image(final_img)
        st.download_button("Görseli İndir", final_img, f"{ticker}_analiz.png", "image/png")
