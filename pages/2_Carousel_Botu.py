import streamlit as st
import yfinance as yf
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import os

# --- 1. AYARLAR ---
FONT_PATH = "Outfit-VariableFont_wght.ttf"
LOGO_PATH = "finanszone 1.png"

# --- 2. VERİ VE AI MOTORU ---
def get_market_data():
    symbols = {"BIST 100": "XU100.IS", "USD/TRY": "USDTRY=X", "Gram Altın": "GC=F", "BIST Banka": "XBANK.IS"}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    results = {}
    for name, ticker in symbols.items():
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if len(df) >= 2:
                open_p = float(df['Open'].iloc[0])
                close_p = float(df['Close'].iloc[-1])
                change = ((close_p - open_p) / open_p) * 100
                results[name] = f"{'+' if change > 0 else ''}{round(change, 2)}%"
            else: results[name] = "N/A"
        except: results[name] = "Hata"
    return results

def generate_ai_headline(data):
    try:
        bist_change = float(data.get("BIST 100", "0%").replace("%", ""))
        bist_status = "BIST-100 haftayı yükselişle kapattı." if bist_change > 0 else "Borsada bu hafta kar satışları görüldü."
        return f"{bist_status}\nPiyasalarda veri trafiği yoğundu."
    except: return "Haftalık piyasa analizi ve\nkritik veriler hazırlandı."

# --- 3. MANUEL BONCUK ÇİZİCİ (Çarpı Hatasına Son) ---
def draw_pagination_dots(draw, current_page, total_pages, w, h, accent_color):
    dot_radius = 8
    spacing = 30
    total_width = (total_pages - 1) * spacing
    start_x = (w - total_width) / 2
    y = h - 100
    
    for i in range(total_pages):
        x = start_x + (i * spacing)
        if i == current_page:
            # Dolu Daire
            draw.ellipse([x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius], fill=accent_color)
        else:
            # Boş Daire (Çerçeve)
            draw.ellipse([x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius], outline=accent_color, width=2)

# --- 4. KAPAK TASARIMI (Daraltılmış Metinler) ---
def create_cover_slide(date_range, headline, is_dark=True):
    w, h = 1080, 1080
    bg_color = (19, 23, 34) if is_dark else (255, 255, 255)
    txt_color = (255, 255, 255) if is_dark else (0, 0, 0)
    accent_color = (38, 166, 154)
    
    img = Image.new('RGB', (w, h), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Font boyutları sığması için küçültüldü
    f_title = ImageFont.truetype(FONT_PATH, 80) # 100 -> 80 yapıldı (Taşmayı önlemek için)
    f_date = ImageFont.truetype(FONT_PATH, 42)
    f_headline = ImageFont.truetype(FONT_PATH, 50)

    # Logo
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_w = 350
        logo_h = int(logo.size[1] * (logo_w / logo.size[0]))
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
        img.paste(logo, (int((w - logo_w) / 2), 150), logo)
        start_y = 150 + logo_h + 80
    except: start_y = 400

    # Başlık (Tam Ortalanmış)
    title_text = "HAFTALIK PİYASA KARNESİ"
    t_bbox = draw.textbbox((0, 0), title_text, font=f_title)
    draw.text(((w - (t_bbox[2]-t_bbox[0]))/2, start_y), title_text, fill=txt_color, font=f_title)
    
    # Tarih (Tam Ortalanmış)
    date_text = f"Tarih: {date_range}"
    d_bbox = draw.textbbox((0, 0), date_text, font=f_date)
    draw.text(((w - (d_bbox[2]-d_bbox[0]))/2, start_y + 100), date_text, fill=(130, 130, 130), font=f_date)

    # Manşet Alanı (Daha içeriden - margin arttırıldı)
    margin = 120
    draw.rectangle([margin, 700, margin + 250, 710], fill=accent_color)
    draw.multiline_text((margin, 740), headline, fill=txt_color, font=f_headline, spacing=15, align="left")
    
    # Boncuklar (Çizim Fonksiyonu ile)
    draw_pagination_dots(draw, 0, 5, w, h, accent_color)
    
    path = f"cover_{datetime.now().strftime('%H%M%S')}.png"
    img.save(path)
    return path

# --- 5. SLAYT 2: VERİLER (Renkli ve Bold) ---
def create_data_slide(market_data, is_dark=True):
    w, h = 1080, 1080
    bg_color = (19, 23, 34) if is_dark else (255, 255, 255)
    txt_color = (255, 255, 255) if is_dark else (0, 0, 0)
    card_bg = (30, 36, 50) if is_dark else (240, 242, 246)
    up_color = (38, 166, 154) # Yeşil
    down_color = (255, 82, 82) # Kırmızı
    
    img = Image.new('RGB', (w, h), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Değerler için Bold etkisi yaratmak adına fontu büyük tutuyoruz
    f_header = ImageFont.truetype(FONT_PATH, 70)
    f_label = ImageFont.truetype(FONT_PATH, 48)
    f_value_bold = ImageFont.truetype(FONT_PATH, 70) # Bold değerler için büyük font

    # Başlık
    draw.text((80, 80), "PİYASA PERFORMANSI", fill=txt_color, font=f_header)
    draw.rectangle([80, 170, 300, 180], fill=up_color)

    # Kartlar
    start_y, card_h, spacing = 250, 160, 35
    for i, (label, value) in enumerate(market_data.items()):
        curr_y = start_y + (i * (card_h + spacing))
        draw.rounded_rectangle([80, curr_y, w - 80, curr_y + card_h], radius=20, fill=card_bg)
        draw.text((120, curr_y + 50), label, fill=(180, 180, 180), font=f_label)
        
        # Renk Kontrolü Geri Geldi
        is_up = "+" in value
        v_color = up_color if is_up else down_color
        
        # Değer Yazımı (Sağa yaslı ve Büyük/Bold hissi)
        v_bbox = draw.textbbox((0, 0), value, font=f_value_bold)
        v_w = v_bbox[2] - v_bbox[0]
        draw.text((w - v_w - 120, curr_y + 40), value, fill=v_color, font=f_value_bold)

    # Boncuklar (Çizim Fonksiyonu ile - Sayfa 2)
    draw_pagination_dots(draw, 1, 5, w, h, up_color)
    
    path = f"data_{datetime.now().strftime('%H%M%S')}.png"
    img.save(path)
    return path

# --- 6. STREAMLIT UI ---
st.set_page_config(page_title="FinansZone Carousel", layout="wide")
if "carousel_history" not in st.session_state: st.session_state.carousel_history = []

st.title("🎠 FinansZone Carousel Botu")

with st.sidebar:
    st.header("⚙️ Ayarlar")
    date_input = st.text_input("Tarih Aralığı", value=datetime.now().strftime("%d.%m.%Y"))
    theme = st.radio("Tema", ["Karanlık", "Aydınlık"])
    if st.button("🗑️ Temizle"):
        st.session_state.carousel_history = []
        st.rerun()

if st.button("🚀 Carousel Paketini Hazırla"):
    with st.spinner("Analiz ediliyor..."):
        data = get_market_data()
        headline = generate_ai_headline(data)
        
        s1 = create_cover_slide(date_input, headline, theme == "Karanlık")
        s2 = create_data_slide(data, theme == "Karanlık")
        
        st.session_state.carousel_history.insert(0, {"pages": [s1, s2], "date": date_input})
        st.rerun()

for entry in st.session_state.carousel_history:
    with st.container():
        st.subheader(f"📊 {entry['date']} Karnesi")
        cols = st.columns(2)
        for i, p_path in enumerate(entry['pages']):
            with cols[i]:
                st.image(p_path, use_container_width=True)
                with open(p_path, "rb") as f:
                    st.download_button(f"📥 Sayfa {i+1}", f, f"Slayt_{i+1}.png", key=p_path)
        st.divider()
