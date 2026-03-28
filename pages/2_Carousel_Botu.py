import streamlit as st
import yfinance as yf
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import os

# --- 1. AYARLAR ---
FONT_PATH = "Outfit-VariableFont_wght.ttf"
LOGO_PATH = "finanszone 1.png"

# --- 2. AI MANŞET MOTORU (Veriye Göre Çıkarım Yapar) ---
def generate_ai_headline(data):
    try:
        bist_change = float(data.get("BIST 100", "0%").replace("%", ""))
        usd_change = float(data.get("USD/TRY", "0%").replace("%", ""))
        
        if bist_change > 1.5:
            bist_status = "BIST-100 haftayı güçlü bir yükselişle kapattı."
        elif bist_change < -1.5:
            bist_status = "Borsada bu hafta satış baskısı hakimdi."
        else:
            bist_status = "Piyasalarda bu hafta yatay bir seyir izlendi."
            
        if usd_change > 0.5:
            curr_status = "Döviz kurlarında yukarı yönlü hareket hızlandı."
        else:
            curr_status = "Küresel piyasalarda veri akışı takibimizdeydi."
            
        return f"{bist_status}\n{curr_status}"
    except:
        return "Haftalık piyasa verileri ve kritik\ngelişmeler analiz edildi."

# --- 3. VERİ ÇEKME ---
def get_market_data():
    symbols = {"BIST 100": "XU100.IS", "USD/TRY": "USDTRY=X", "Gram Altın": "GC=F", "BIST Banka": "XBANK.IS"}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    results = {}
    for name, ticker in symbols.items():
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if len(df) >= 2:
                change = ((float(df['Close'].iloc[-1]) - float(df['Open'].iloc[0])) / float(df['Open'].iloc[0])) * 100
                results[name] = f"{'+' if change > 0 else ''}{round(change, 2)}%"
            else: results[name] = "N/A"
        except: results[name] = "Hata"
    return results

# --- 4. KAPAK TASARIMI (Hizalamalar Düzeltildi) ---
def create_cover_slide(date_range, headline, is_dark=True):
    w, h = 1080, 1080
    bg_color = (19, 23, 34) if is_dark else (255, 255, 255)
    txt_color = (255, 255, 255) if is_dark else (0, 0, 0)
    accent_color = (38, 166, 154)
    
    img = Image.new('RGB', (w, h), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    f_title = ImageFont.truetype(FONT_PATH, 95)
    f_date = ImageFont.truetype(FONT_PATH, 42)
    f_headline = ImageFont.truetype(FONT_PATH, 52)
    f_dots = ImageFont.truetype(FONT_PATH, 50)

    # 1. LOGO (Merkezi)
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_w = 400
        logo_h = int(logo.size[1] * (logo_w / logo.size[0]))
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
        img.paste(logo, (int((w - logo_w) / 2), 120), logo)
        start_y = 120 + logo_h + 60
    except: start_y = 300

    # 2. BAŞLIK (Merkezi Hizalama Düzeltildi)
    title_text = "HAFTALIK PİYASA KARNESİ"
    t_bbox = draw.textbbox((0, 0), title_text, font=f_title)
    draw.text(((w - (t_bbox[2]-t_bbox[0]))/2, start_y), title_text, fill=txt_color, font=f_title)
    
    # 3. TARİH (Merkezi)
    date_text = f"Tarih: {date_range}"
    d_bbox = draw.textbbox((0, 0), date_text, font=f_date)
    draw.text(((w - (d_bbox[2]-d_bbox[0]))/2, start_y + 120), date_text, fill=(130, 130, 130), font=f_date)

    # 4. MANŞET (Sol Kenara Yaslı, Şık Kutu İçinde)
    # Manşet Alanı - Alt Kısım
    margin = 80
    draw.rectangle([margin, 700, margin + 250, 712], fill=accent_color) # Yeşil ayraç
    draw.multiline_text((margin, 740), headline, fill=txt_color, font=f_headline, spacing=15)
    
    # 5. BONCUKLAR (Merkezi)
    dots_text = "● ○ ○ ○ ○"
    dots_bbox = draw.textbbox((0, 0), dots_text, font=f_dots)
    draw.text(((w - (dots_bbox[2]-dots_bbox[0]))/2, h - 80), dots_text, fill=accent_color, font=f_dots)
    
    path = f"cover_{datetime.now().strftime('%H%M%S')}.png"
    img.save(path)
    return path

# --- 5. SLAYT 2: PİYASA VERİLERİ ---
def create_data_slide(market_data, is_dark=True):
    w, h = 1080, 1080
    bg_color = (19, 23, 34) if is_dark else (255, 255, 255)
    txt_color = (255, 255, 255) if is_dark else (0, 0, 0)
    card_bg = (30, 36, 50) if is_dark else (240, 242, 246)
    accent_color = (38, 166, 154)
    loss_color = (255, 82, 82)
    
    img = Image.new('RGB', (w, h), color=bg_color)
    draw = ImageDraw.Draw(img)
    f_header, f_label, f_value, f_dots = ImageFont.truetype(FONT_PATH, 75), ImageFont.truetype(FONT_PATH, 48), ImageFont.truetype(FONT_PATH, 65), ImageFont.truetype(FONT_PATH, 50)

    draw.text((80, 80), "PİYASA PERFORMANSI", fill=txt_color, font=f_header)
    draw.rectangle([80, 175, 300, 185], fill=accent_color)

    start_y, card_h, spacing = 250, 160, 30
    for i, (label, value) in enumerate(market_data.items()):
        curr_y = start_y + (i * (card_h + spacing))
        draw.rounded_rectangle([80, curr_y, w - 80, curr_y + card_h], radius=20, fill=card_bg)
        draw.text((130, curr_y + 50), label, fill=(180, 180, 180), font=f_label)
        v_color = accent_color if "+" in value else loss_color
        v_bbox = draw.textbbox((0, 0), value, font=f_value)
        draw.text((w - (v_bbox[2]-v_bbox[0]) - 130, curr_y + 42), value, fill=v_color, font=f_value)

    dots_text = "○ ● ○ ○ ○"
    dots_bbox = draw.textbbox((0, 0), dots_text, font=f_dots)
    draw.text(((w - (dots_bbox[2]-dots_bbox[0]))/2, h - 80), dots_text, fill=accent_color, font=f_dots)
    path = f"data_{datetime.now().strftime('%H%M%S')}.png"
    img.save(path)
    return path

# --- 6. STREAMLIT UI ---
st.set_page_config(page_title="FinansZone Carousel", layout="wide")
if "carousel_history" not in st.session_state: st.session_state.carousel_history = []

st.title("🎠 FinansZone Otomatik Carousel")

with st.sidebar:
    st.header("⚙️ Kontrol Paneli")
    date_input = st.text_input("Tarih Aralığı", value=datetime.now().strftime("%d - %m %Y"))
    st.info("Manşet, verilere göre otomatik oluşturulacaktır.")
    theme = st.radio("Tema", ["Karanlık", "Aydınlık"])
    if st.button("🗑️ Geçmişi Temizle"):
        st.session_state.carousel_history = []
        st.rerun()

if st.button("🚀 Carousel Paketini Hazırla"):
    with st.spinner("Piyasa taranıyor ve analiz ediliyor..."):
        data = get_market_data()
        auto_headline = generate_ai_headline(data) # AI Manşeti burada oluşuyor
        
        slide1 = create_cover_slide(date_input, auto_headline, theme == "Karanlık")
        slide2 = create_data_slide(data, theme == "Karanlık")
        
        st.session_state.carousel_history.insert(0, {
            "pages": [slide1, slide2],
            "date": date_input,
            "headline": auto_headline
        })
        st.rerun()

for entry in st.session_state.carousel_history:
    with st.container():
        st.subheader(f"📊 {entry['date']} Karnesi")
        st.write(f"**Otomatik Analiz:** {entry['headline']}")
        cols = st.columns(len(entry['pages']))
        for i, p_path in enumerate(entry['pages']):
            with cols[i]:
                st.image(p_path, use_container_width=True)
                with open(p_path, "rb") as f:
                    st.download_button(f"📥 Sayfa {i+1}", f, f"Slayt_{i+1}.png", key=p_path)
        st.divider()
