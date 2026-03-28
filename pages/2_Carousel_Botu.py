import streamlit as st
import yfinance as yf
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import os

# --- 1. SİSTEM VE VERİ HAZIRLIĞI ---
# Font kontrolü
FONT_PATH = "Outfit-VariableFont_wght.ttf"
if not os.path.exists(FONT_PATH):
    st.error(f"Kritik Hata: '{FONT_PATH}' dosyası ana dizinde bulunamadı. Lütfen font dosyasını GitHub reponuza yükleyin.")
    st.stop()

def get_market_data():
    symbols = {
        "BIST 100": "XU100.IS",
        "USD/TRY": "USDTRY=X",
        "Gram Altın": "GC=F",
        "BIST Banka": "XBANK.IS"
    }
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    results = {}
    for name, ticker in symbols.items():
        try:
            df = yf.download(ticker, start=start_date, end=end_date)
            if len(df) >= 2:
                open_p = float(df['Open'].iloc[0])
                close_p = float(df['Close'].iloc[-1])
                change = ((close_p - open_p) / open_p) * 100
                results[name] = f"{'+' if change > 0 else ''}{round(change, 2)}%"
            else: results[name] = "N/A"
        except: results[name] = "Error"
    return results

# --- 2. GÖRSEL İŞLEME (KAPAK TASARIMCISI REVİZE EDİLDİ) ---
def create_cover_slide(date_range, headline, is_dark=True):
    # 1080x1080 Kare Format
    w, h = 1080, 1080
    bg_color = (19, 23, 34) if is_dark else (255, 255, 255)
    txt_color = (255, 255, 255) if is_dark else (0, 0, 0)
    accent_color = (38, 166, 154) # FinansZone Yeşil Vurgusu
    sub_txt_color = (135, 135, 135)
    
    img = Image.new('RGB', (w, h), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    try:
        # Extra Bold fontlar
        f_title = ImageFont.truetype(FONT_PATH, 110) # Daha büyük başlık
        f_date = ImageFont.truetype(FONT_PATH, 45)
        f_headline = ImageFont.truetype(FONT_PATH, 55) # Manşet fontu
        f_dots = ImageFont.truetype(FONT_PATH, 50) # Boncuk fontu
    except:
        f_title = f_date = f_headline = f_dots = ImageFont.load_default()

    # 1. GÜNCELLEME: LOGO DEV GİBİ VE MERKEZİ
    try:
        logo = Image.open("finanszone 1.png").convert("RGBA")
        # Logoyu büyüt (Örn: 300px genişlik, oranlı yükseklik)
        logo_w_target = 300 
        w_percent = (logo_w_target / float(logo.size[0]))
        logo_h_target = int((float(logo.size[1]) * float(w_percent)))
        logo = logo.resize((logo_w_target, logo_h_target), Image.LANCZOS)
        
        # Logoyu üst merkeze yapıştır (x: (w-lw)/2, y: 80)
        img.paste(logo, (int((w - logo.width) / 2), 80), logo)
        
        # Başlığın Y koordinatını logoya göre ayarla
        title_y = 80 + logo.height + 60
    except:
        # Logo bulunamazsa hata vermemesi için varsayılan Y koordinatına düşer
        title_y = 300

    # 2. Ana Başlık (Extra Bold)
    title_text = "HAFTALIK PİYASA KARNESİ"
    # Metni ortalamak için bbox hesabı
    title_bbox = draw.textbbox((0, 0), title_text, font=f_title)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text((int((w - title_w) / 2), title_y), title_text, fill=txt_color, font=f_title, align="center")
    
    # 3. Tarih Aralığı (Ortalı)
    date_text = f"Tarih: {date_range}"
    date_bbox = draw.textbbox((0, 0), date_text, font=f_date)
    date_w = date_bbox[2] - date_bbox[0]
    draw.text((int((w - date_w) / 2), title_y + 130), date_text, fill=sub_txt_color, font=f_date)

    # 4. GÜNCELLEME: MANŞET/ANALİZ ÖZETİ (Yarıda)
    draw.rectangle([80, 700, w - 80, 715], fill=accent_color) # Yeşil Vurgu Çizgisi
    draw.multiline_text((80, 740), headline, fill=txt_color, font=f_headline, spacing=15, align="left")
    
    # 5. GÜNCELLEME: BONCUKLAR (Özellik 4)
    # 5 Slaytlık bir carousel olduğunu gösteren boncuklar (● ○ ○ ○ ○)
    # Aktif olan ilk boncuk (Kapak sayfasındayız)
    dots_text = "● ○ ○ ○ ○"
    dots_bbox = draw.textbbox((0, 0), dots_text, font=f_dots)
    dots_w = dots_bbox[2] - dots_bbox[0]
    draw.text((int((w - dots_w) / 2), h - 100), dots_text, fill=accent_color, font=f_dots)
    
    final_path = f"Kapak_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(final_path, quality=100)
    return final_path

# --- 3. STREAMLIT UI (OTURUM HAFIZALI) ---
st.set_page_config(page_title="FinansZone Carousel", layout="wide")

# Oturum Hafızasını Başlat
if "carousel_history" not in st.session_state:
    st.session_state.carousel_history = []

st.title("🎠 Haftalık Karne Carousel Akışı")

with st.sidebar:
    st.header("⚙️ Ayarlar")
    date_input = st.text_input("Tarih Aralığı", value="18 - 22 Mart 2024")
    
    # GÜNCELLEME: MANŞET GİRİŞİ (Özellik 2)
    headline_input = st.text_area("Manşet/Analiz Özeti (Kapakta Görülecek)", 
                                  value="BIST-100 haftayı zirvede tamamladı, haftanın yıldızı teknoloji fonları oldu.", 
                                  height=100)
    
    theme = st.radio("Tema", ["Karanlık", "Aydınlık"])
    dark_mode = theme == "Karanlık"
    
    st.markdown("---")
    if st.button("🗑️ Geçmişi Temizle"):
        st.session_state.carousel_history = []
        st.rerun()

    st.markdown("---")
    st.info("Bu araç Carousel formatında 1080x1080 görseller üretir.")

# CAROUSEL HAZIRLA BUTONU
if st.button("🚀 Carousel Hazırla"):
    with st.spinner("Veriler çekiliyor ve kapak tasarlanıyor..."):
        try:
            # 1. Slaytı Oluştur (Kapak)
            cover_img_path = create_cover_slide(date_input, headline_input, dark_mode)
            
            # Oluşturulan kapağı listenin EN BAŞINA ekle (en yeni en üstte)
            st.session_state.carousel_history.insert(0, {
                "path": cover_img_path,
                "date_range": date_input,
                "headline": headline_input,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            st.rerun() # Ekranda hemen göstermek için yenile
            
        except Exception as e:
            st.error(f"Hata oluştu: {e}")

# --- GEÇMİŞ KAPAKLARI EKRANA BASMA (SOHBET AKIŞI) ---
st.divider()
for i, cover in enumerate(st.session_state.carousel_history):
    with st.container():
        st.subheader(f"📊 {cover['date_range']} Karneyi - {cover['timestamp']}")
        
        # Carousel Boncukları ve Aktif Sayfa Bilgisi (Streamlit UI'da)
        # i=0 ise en son oluşturulan, i=1 ise bir önceki
        # Bu bilgi görselin içinde zaten var (Boncuk 1 aktif), burada sadece UI'da teyit ediyoruz.
        st.caption(f"Carousel Sayfa {i+1} / 5 (Kapak)")
        
        st.image(cover['path'], width=500)
        
        with open(cover['path'], "rb") as file:
            st.download_button(
                label=f"📥 {cover['date_range']} Kapağını İndir", 
                data=file, 
                file_name=f"FinansZone_Kapak_{cover['date_range']}.png", 
                mime="image/png",
                key=cover['path'] # Benzersiz anahtar şart
            )
        st.divider()
