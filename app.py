import streamlit as st
import asyncio
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

# --- 1. SİSTEM HAZIRLIĞI ---
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
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        url = f"https://www.tradingview.com/symbols/BIST-{ticker}/?timeframe={selected_tf['url']}"
        await page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(8) 

        if is_dark:
            try:
                await page.get_by_role("button", name="Open user menu").click()
                await asyncio.sleep(1)
                await page.locator("label").filter(has_text="Dark theme").click(force=True)
                await page.evaluate("document.documentElement.classList.add('theme-dark')")
                await page.keyboard.press("Escape")
            except: pass

        try:
            full_name = await page.locator("h1").first.inner_text()
            full_name = full_name.split("Grafiği")[0].strip()
            target_button = page.get_by_role("button", name=re.compile(selected_tf['query'], re.IGNORECASE))
            btn_text = await target_button.inner_text()
            return_rate = re.search(r"[-+−]?\d*[.,]\d+%", btn_text).group() if "%" in btn_text else "0.00%"
        except:
            full_name, return_rate = ticker, "N/A"

        try:
            await page.get_by_role("button", name="Take a snapshot").click()
            await asyncio.sleep(1)
            async with page.expect_download() as download_info:
                await page.get_by_role("row", name="Download image").click()
            download = await download_info.value
            temp_path = f"temp_{ticker}.png"
            await download.save_as(temp_path)
        except:
            temp_path = f"temp_{ticker}.png"
            await page.screenshot(path=temp_path, clip={'x': 300, 'y': 200, 'width': 1200, 'height': 600})

        await browser.close()
        return temp_path, {"name": full_name, "ticker": ticker, "range": timeframe_text, "return": return_rate, "dark": is_dark}

# --- 3. GÖRSEL İŞLEME (ALT-ÜST UZATMA VE LOGO KONTROLÜ) ---
def finalize_image(path, data, show_logo):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    
    # TV kenarlıklarını temizle
    img = img.crop((0, 20, w, h - 40)) 
    
    header_h = 160 
    footer_h = 100 if show_logo else 40 # Logo varsa footer'ı büyütüyoruz
    
    bg_color = (19, 23, 34) if data['dark'] else (255, 255, 255)
    
    # Yeni imaj oluştur: Üstte header, ortada grafik, altta footer boşluğu
    new_img = Image.new('RGB', (w, img.height + header_h + footer_h), color=bg_color)
    new_img.paste(img, (0, header_h))
    
    draw = ImageDraw.Draw(new_img)
    txt_color = (255, 255, 255) if data['dark'] else (0, 0, 0)
    sub_txt_color = (135, 135, 135)

    raw_ret = data['return']
    is_neg = "-" in raw_ret or "−" in raw_ret or "negative" in raw_ret.lower()
    accent = (255, 82, 82) if is_neg else (38, 166, 154)

    try:
        f_main = ImageFont.truetype("Outfit-VariableFont_wght.ttf", 55) 
        f_sub = ImageFont.truetype("Outfit-VariableFont_wght.ttf", 32)
    except:
        f_main = f_sub = ImageFont.load_default()

    # ÜST KISIM (Header)
    draw.text((45, 35), data['name'].upper(), fill=txt_color, font=f_main)
    draw.text((45, 105), f"{data['ticker']}  |  {data['range']}", fill=sub_txt_color, font=f_sub)
    
    bbox = draw.textbbox((0, 0), raw_ret, font=f_main)
    return_w = bbox[2] - bbox[0]
    draw.text((w - return_w - 45, 35), raw_ret, fill=accent, font=f_main, stroke_width=1, stroke_fill=accent)
    
    # --- ALT KISIM (Footer) VE LOGO EKLEME ---
    if show_logo:
        try:
            logo = Image.open("finanszone 1.png").convert("RGBA")
            # Logoyu footer'a sığacak şekilde küçült (70px yükseklik)
            base_h = 70 
            w_percent = (base_h / float(logo.size[1]))
            base_w = int((float(logo.size[0]) * float(w_percent)))
            logo = logo.resize((base_w, base_h), Image.LANCZOS)
            
            # Logoyu SAĞ ALT köşeye yapıştır
            logo_x = w - logo.width - 45
            logo_y = new_img.height - logo.height - 15
            new_img.paste(logo, (logo_x, logo_y), logo)
        except:
            pass # Logo dosyası yoksa sessizce devam et

    final_path = f"Final_{data['ticker']}.png"
    new_img.save(final_path, quality=100)
    return final_path

# --- 4. STREAMLIT UI ---
st.set_page_config(page_title="FinansZone Rapor", layout="centered")

st.title("📈 FinansZone Rapor Oluşturucu")

today_str = datetime.now().strftime("%Y-%m-%d")

with st.sidebar:
    st.header("⚙️ Hisse Seç")
    symbol = st.text_input("Hisse Sembolü", value="THYAO")
    timeframe = st.selectbox("Zaman Aralığı", ["1 gün", "5 gün", "1 ay", "6 ay", "YTD", "1 yıl", "5 yıl", "Tümü"])
    theme = st.radio("Tema", ["Aydınlık", "Karanlık"])
    dark_mode = theme == "Karanlık"
    
    st.markdown("---")
    # LOGO SEÇENEĞİ BURADA
    show_logo = st.checkbox("Görselde Logo Olsun", value=True)
    
    st.markdown("---")
    st.markdown("### Made with <3 by Emir")

if st.button("🚀 Raporu Hazırla"):
    with st.spinner("İşlem yapılıyor, lütfen bekleyin..."):
        try:
            raw_path, info = asyncio.run(fetch_tradingview_report(symbol, timeframe, dark_mode))
            # show_logo bilgisini finalize_image'a gönderiyoruz
            final_report = finalize_image(raw_path, info, show_logo)
            
            st.success(f"✅ {symbol} Raporu Hazır!")
            st.image(final_report)
            
            with open(final_report, "rb") as file:
                st.download_button(
                    label="📥 Görseli İndir", 
                    data=file, 
                    file_name=f"{symbol}_Rapor_{today_str}.png", 
                    mime="image/png"
                )
            
            if os.path.exists(raw_path): os.remove(raw_path)
        except Exception as e:
            st.error(f"Hata oluştu: {e}")

st.divider()
st.caption(f"FinansZone • {today_str}")
