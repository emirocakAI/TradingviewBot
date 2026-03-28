import streamlit as st
import asyncio
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

# --- 1. SİSTEM VE SAYAÇ HAZIRLIĞI ---
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

# Kalıcı sayaç için dosya kontrolü
COUNTER_FILE = "counter.txt"

def get_total_count():
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "w") as f:
            f.write("0")
        return 0
    with open(COUNTER_FILE, "r") as f:
        try:
            return int(f.read().strip())
        except:
            return 0

def increment_total_count():
    current = get_total_count()
    new_count = current + 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(new_count))
    return new_count

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
            timestamp = datetime.now().strftime("%H%M%S")
            temp_path = f"temp_{ticker}_{timestamp}.png"
            await download.save_as(temp_path)
        except:
            timestamp = datetime.now().strftime("%H%M%S")
            temp_path = f"temp_{ticker}_{timestamp}.png"
            await page.screenshot(path=temp_path, clip={'x': 300, 'y': 200, 'width': 1200, 'height': 600})

        await browser.close()
        return temp_path, {"name": full_name, "ticker": ticker, "range": timeframe_text, "return": return_rate, "dark": is_dark}

# --- 3. GÖRSEL İŞLEME ---
def finalize_image(path, data, show_logo):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    img = img.crop((0, 20, w, h - 40)) 
    
    header_h = 160 
    footer_h = 100 if show_logo else 40 
    
    bg_color = (19, 23, 34) if data['dark'] else (255, 255, 255)
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

    draw.text((45, 35), data['name'].upper(), fill=txt_color, font=f_main)
    draw.text((45, 105), f"{data['ticker']}  |  {data['range']}", fill=sub_txt_color, font=f_sub)
    
    bbox = draw.textbbox((0, 0), raw_ret, font=f_main)
    return_w = bbox[2] - bbox[0]
    draw.text((w - return_w - 45, 35), raw_ret, fill=accent, font=f_main, stroke_width=1, stroke_fill=accent)
    
    if show_logo:
        try:
            logo = Image.open("finanszone 1.png").convert("RGBA")
            base_h = 150 
            w_percent = (base_h / float(logo.size[1]))
            base_w = int((float(logo.size[0]) * float(w_percent)))
            logo = logo.resize((base_w, base_h), Image.LANCZOS)
            logo_x = w - logo.width - 45
            logo_y = new_img.height - logo.height - 15
            new_img.paste(logo, (logo_x, logo_y), logo)
        except:
            pass 

    final_path = f"Final_{data['ticker']}_{datetime.now().strftime('%H%M%S')}.png"
    new_img.save(final_path, quality=100)
    return final_path

# --- 4. STREAMLIT UI ---
st.set_page_config(page_title="FinansZone Rapor", layout="centered")

if "report_history" not in st.session_state:
    st.session_state.report_history = []

st.title("📈 FinansZone Rapor Akışı")

with st.sidebar:
    st.header("⚙️ Hisse Seç")
    symbol = st.text_input("Hisse Sembolü", value="THYAO")
    timeframe = st.selectbox("Zaman Aralığı", ["1 gün", "5 gün", "1 ay", "6 ay", "YTD", "1 yıl", "5 yıl", "Tümü"])
    theme = st.radio("Tema", ["Aydınlık", "Karanlık"])
    dark_mode = theme == "Karanlık"
    
    st.markdown("---")
    show_logo = st.checkbox("Görselde Logo Olsun", value=True)
    
    if st.button("🗑️ Geçmişi Temizle"):
        st.session_state.report_history = []
        st.rerun()

    st.markdown("---")
    # SAYAÇ BURADA
    total_count = get_total_count()
    st.write(f"📊 Şimdiye kadar **{total_count}** hisse grafiği oluşturuldu.")
    
    st.markdown("### Made with <3 by Emir")

if st.button("🚀 Raporu Hazırla"):
    with st.spinner(f"{symbol} raporu hazırlanıyor..."):
        try:
            raw_path, info = asyncio.run(fetch_tradingview_report(symbol, timeframe, dark_mode))
            final_report = finalize_image(raw_path, info, show_logo)
            
            # Sayaç artır
            increment_total_count()
            
            st.session_state.report_history.insert(0, {
                "path": final_report,
                "ticker": symbol,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            
            if os.path.exists(raw_path): os.remove(raw_path)
            st.rerun() # Sayacı güncellemek için sayfayı yenile
            
        except Exception as e:
            st.error(f"Hata oluştu: {e}")

st.divider()
for report in st.session_state.report_history:
    with st.container():
        st.subheader(f"📊 {report['ticker']} - {report['date']}")
        st.image(report['path'])
        with open(report['path'], "rb") as file:
            st.download_button(
                label=f"📥 {report['ticker']} İndir", 
                data=file, 
                file_name=f"{report['ticker']}_Rapor.png", 
                mime="image/png",
                key=report['path']
            )
        st.divider()
