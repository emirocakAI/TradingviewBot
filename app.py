import os
import asyncio
import re
import streamlit as st
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# --- 1. SİSTEM VE FONT AYARLARI ---
# Streamlit sunucusunda tarayıcıyı kur
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

FONT_PATH = "Outfit-VariableFont_wght.ttf"

def get_styled_fonts():
    try:
        # Şirket: Semibold 24 | Getiri: Black 26 (Dolgunluk için)
        return ImageFont.truetype(FONT_PATH, 24), ImageFont.truetype(FONT_PATH, 26)
    except:
        # Font bulunamazsa hata vermemesi için varsayılanı yükle
        return ImageFont.load_default(), ImageFont.load_default()

# --- 2. TEMİZ SNAPSHOT (KAMERA) URL'SİNİ YAKALAMA ---
async def fetch_clean_snapshot_url(ticker, period_label, theme):
    async with async_playwright() as p:
        # Bot korumasını aşmak için kullanıcı gibi davranan argümanlar
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        
        # Tema seçimine göre zorunlu renk şeması (dark/light)
        color_scheme = "dark" if theme == "Dark Mod" else "light"
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            color_scheme=color_scheme
        )
        
        page = await context.new_page()
        # Manuel Stealth: Webdriver parametresini sil
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # TradingView Sembol Sayfası
        await page.goto(f"https://www.tradingview.com/symbols/BIST-{ticker}/", wait_until="networkidle")
        await asyncio.sleep(5) # Verilerin tam yüklenmesi için bekleme
        
        try:
            # Otomatik Şirket İsmi
            raw_name = await page.locator("h1").first.inner_text()
            company_name = raw_name.split("Grafiği")[0].strip()
            
            # Zaman Periyodu Butonuna Tıkla ve Getiriyi Al
            period_button = page.get_by_role("button", name=re.compile(period_label, re.IGNORECASE))
            await period_button.click()
            await asyncio.sleep(2)
            btn_text = await period_button.inner_text()
            yield_val = re.search(r"[-+]?\d*[.,]\d+%", btn_text).group() if "%" in btn_text else "0.00%"
            
            # DARK MODE ZORLAMASI (Sayfa içine class enjekte ederek)
            if theme == "Dark Mod":
                await page.evaluate("document.documentElement.classList.add('theme-dark')")
                await asyncio.sleep(1)

            # --- KRİTİK ADIM: KAMERA BUTONUNA BAS VE URL'Yİ YAKALA ---
            # TradingView mini chart üzerindeki kamera ikonuna basıyoruz
            async with page.expect_popup() as popup_info:
                # 'take-a-snapshot' butonunu bul ve tıkla
                camera_button = page.locator("[data-name='take-a-snapshot']").first
                await camera_button.scroll_into_view_if_needed()
                await camera_button.click()
            
            # Açılan yeni sekmenin (snapshot URL) içeriğini yakala
            snapshot_page = await popup_info.value
            await snapshot_page.wait_for_load_state("networkidle")
            
            # Saf resim elementine odaklan ve screenshot al (en temiz yöntem budur)
            pure_chart_bytes = await snapshot_page.locator("img").screenshot()
            await browser.close()
            return pure_chart_bytes, company_name, yield_val

        except Exception as e:
            # Hata anında tüm sayfa yerine en azından ana alanı kurtarmaya çalışalım
            st.warning(f"Detaylı çekim yapılamadı, genel görünüm alınıyor. Hata: {e}")
            img_bytes = await page.screenshot(clip={'x': 0, 'y': 150, 'width': 1200, 'height': 600})
            await browser.close()
            return img_bytes, ticker, "Hata"

# --- 3. GÖRSELİ İŞLEME VE FONT BASMA ---
def process_final_image(img_bytes, company, period, yield_val, theme):
    img = Image.open(BytesIO(img_bytes))
    draw = ImageDraw.Draw(img)
    f_semi, f_black = get_styled_fonts()
    
    # Tema renk ayarları
    txt_color = "black" if theme == "Beyaz Mod" else "white"
    yield_color = "#089981" if "-" not in yield_val else "#f23645" # Yeşil / Kırmızı
    
    # Metinleri sol üst köşeye yerleştirme (Dolgun Outfit Fontları ile)
    # Şirket İsmi: Semibold (40, 40)
    draw.text((40, 40), str(company).upper(), font=f_semi, fill=txt_color)
    # Tarih ve Getiri: Black (40, 85)
    draw.text((40, 85), f"{period} Getiri: {yield_val}", font=f_black, fill=yield_color)
    
    # İşlenmiş görseli buffer'a kaydet
    output = BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()

# --- 4. STREAMLIT ARAYÜZÜ ---
st.set_page_config(page_title="FinansZone Snapshot", layout="centered")
st.title("📸 FinansZone Temiz Grafik Botu")

# Kullanıcıdan istediğimiz 3 soru:
ticker = st.text_input("Hisse Kodu (Örn: THYAO):", "THYAO").upper()
period = st.selectbox("Tarih Aralığı:", ["1 day", "5 days", "1 month", "6 months", "Year to date", "1 year", "All time"])
theme = st.radio("Tema Seçimi:", ["Beyaz Mod", "Dark Mod"], horizontal=True)

if st.button("🚀 Grafiği Temiz Yakala"):
    with st.spinner(f"Colab kalitesinde, {theme} grafik hazırlanıyor..."):
        try:
            # 1. Kamera butonu ile saf resmi yakala
            img_raw, name, y_val = asyncio.run(fetch_clean_snapshot_url(ticker, period, theme))
            
            # 2. Üzerine fontları bas
            final_report = process_final_image(img_raw, name, period, y_val, theme)
            
            # 3. Sonucu göster
            st.success(f"Analiz Tamamlandı: {name}")
            st.image(final_report)
            
            with open("rapor.png", "wb") as f:
                f.write(final_report)
            st.download_button("📥 Görseli Kaydet", final_report, file_name=f"FinansZone_{ticker}.png")
            
        except Exception as e:
            st.error(f"Sistem bir engelle karşılaştı: {e}")
