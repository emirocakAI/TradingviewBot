import os
import asyncio
import re
import streamlit as st
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# --- 1. SİSTEM VE FONT ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

FONT_PATH = "Outfit-VariableFont_wght.ttf"

def get_styled_fonts():
    try:
        return ImageFont.truetype(FONT_PATH, 24), ImageFont.truetype(FONT_PATH, 26)
    except:
        return ImageFont.load_default(), ImageFont.load_default()

# --- 2. NOKTA ATIŞI SNAPSHOT (KAMERA) FONKSİYONU ---
async def get_clean_tv_image(ticker, period_label, theme):
    async with async_playwright() as p:
        # Bot korumasını aşmak için kullanıcı gibi davranıyoruz
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # 1. Sayfaya Git
        await page.goto(f"https://www.tradingview.com/symbols/BIST-{ticker}/", wait_until="networkidle")
        await asyncio.sleep(5)
        
        try:
            # 2. Dark Mode Ayarı (Dom'a müdahale)
            if theme == "Dark Mod":
                await page.evaluate("document.documentElement.classList.add('theme-dark')")
            
            # 3. Verileri Çek
            company_name = (await page.locator("h1").first.inner_text()).split("Grafiği")[0].strip()
            period_btn = page.get_by_role("button", name=re.compile(period_label, re.IGNORECASE))
            await period_btn.click()
            await asyncio.sleep(2)
            btn_text = await period_btn.inner_text()
            yield_val = re.search(r"[-+]?\d*[.,]\d+%", btn_text).group() if "%" in btn_text else "0.00%"

            # 4. KAMERA BUTONUNA NOKTA ATIŞI (Snapshot)
            # TradingView'ın kamera butonuna basıp resim linkini alıyoruz
            await page.click("[data-name='take-a-snapshot']")
            # Açılan menüden "Resmi yeni sekmede aç" veya "Resim linkini kopyala" yerine 
            # direkt o anki temiz chart alanının screenshot'ını alıyoruz (en stabil yol bu)
            chart_element = page.locator(".tv-category-header__price-chart, [class*='chartContainer-']").first
            img_bytes = await chart_element.screenshot()
            
            return img_bytes, company_name, yield_val
        
        except Exception as e:
            # Hata anında tüm sayfa yerine en azından ana alanı kurtaralım
            img_bytes = await page.screenshot(clip={'x': 0, 'y': 150, 'width': 1200, 'height': 600})
            return img_bytes, ticker, "Hata"
        finally:
            await browser.close()

# --- 3. GÖRSELİ İŞLEME ---
def process_report(img_bytes, company, period, yield_val, theme):
    img = Image.open(BytesIO(img_bytes))
    draw = ImageDraw.Draw(img)
    f_semi, f_black = get_styled_fonts()
    
    txt_color = "white" if theme == "Dark Mod" else "black"
    y_color = "#089981" if "-" not in yield_val else "#f23645"
    
    # Yazıları bas
    draw.text((40, 40), company.upper(), font=f_semi, fill=txt_color)
    draw.text((40, 85), f"{period} Getiri: {yield_val}", font=f_black, fill=y_color)
    
    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()

# --- 4. STREAMLIT ---
st.title("🚀 FinansZone Nokta Atışı Rapor")
ticker = st.text_input("Hisse:", "THYAO").upper()
period = st.selectbox("Periyot:", ["1 month", "6 months", "Year to date", "1 year"])
theme = st.radio("Tema:", ["Beyaz Mod", "Dark Mod"])

if st.button("Raporu Al"):
    with st.spinner("Colab kalitesinde veri çekiliyor..."):
        img_raw, c_name, y_val = asyncio.run(get_clean_tv_image(ticker, period, theme))
        final = process_report(img_raw, c_name, period, y_val, theme)
        st.image(final)
        st.download_button("İndir", final, "rapor.png")
