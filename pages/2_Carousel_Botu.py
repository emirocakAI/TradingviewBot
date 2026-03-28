import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import io

# --- 1. AYARLAR & EVDS FONKSİYONU ---
EVDS_KEY = "8nTja3zQFQ"
FONT_PATH = "Outfit-VariableFont_wght.ttf" # Font dosyasının konumundan emin ol
LOGO_PATH = "finanszone 1.png"
W, H = 1080, 1080

@st.cache_data(ttl=3600)
def get_pro_metrics():
    try:
        from evds import evdsAPI
        evds = evdsAPI(EVDS_KEY)
        end_date = datetime.now().strftime('%d-%m-%Y')
        start_date = (datetime.now() - timedelta(days=15)).strftime('%d-%m-%Y')
        
        # TP.AB.G02: Rezerv, TP.DK.USD.A.YTL: Dolar
        df = evds.get_data(['TP.AB.G02', 'TP.DK.USD.A.YTL'], startdate=start_date, enddate=end_date)
        df = df.ffill().dropna() # Hafta sonu boşluğunu doldur
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        return {
            "rezerv": f"{round(latest['TP.AB.G02']/1000, 2)}B$",
            "rezerv_degisim": latest['TP.AB.G02'] - prev['TP.AB.G02'],
            "dolar_tcmb": round(latest['TP.DK.USD.A.YTL'], 4)
        }
    except:
        return None

# --- 2. TASARIM ARAÇLARI ---
def get_safe_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()

def draw_pagination(draw, active_step):
    dot_radius = 8
    spacing = 30
    start_x = (W - (4 * spacing)) / 2
    for i in range(5):
        color = (38, 166, 154) if i == active_step else (100, 100, 100)
        draw.ellipse([start_x + i*spacing, 1000, start_x + i*spacing + dot_radius*2, 1000 + dot_radius*2], fill=color)

# --- 3. SAYFA OLUŞTURUCULAR (S5 VE EVDS ÖZEL) ---

def create_s3_evds(data, is_dark):
    # EVDS Verileriyle Makro Bakış Sayfası
    bg = (19, 23, 34) if is_dark else (255, 255, 255)
    txt_c = (255, 255, 255) if is_dark else (0, 0, 0)
    img = Image.new('RGB', (W, H), color=bg)
    draw = ImageDraw.Draw(img)
    
    # Başlık
    draw.text((80, 100), "MERKEZ BANKASI RAPORU", fill=(38, 166, 154), font=get_safe_font(60))
    
    # Rezerv Kutusu
    draw.rounded_rectangle([80, 250, W-80, 500], radius=30, fill=(30, 36, 50) if is_dark else (240, 240, 240))
    draw.text((120, 280), "TCMB Brüt Rezervleri", fill=(150, 150, 150), font=get_safe_font(40))
    draw.text((120, 340), data['rezerv'], fill=(38, 166, 154), font=get_safe_font(100))
    
    # Yorum
    msg = "Rezervlerdeki haftalık değişim piyasa\nlikiditesi açısından pozitif seyrediyor."
    draw.multiline_text((80, 600), msg, fill=txt_c, font=get_safe_font(45), spacing=15)
    
    draw_pagination(draw, 2)
    return img

def create_s5_final(is_dark):
    # Senin "kötü duruyor" dediğin logoyu düzelttiğimiz final sayfası
    bg = (19, 23, 34) if is_dark else (255, 255, 255)
    txt_c = (255, 255, 255) if is_dark else (0, 0, 0)
    img = Image.new('RGB', (W, H), color=bg)
    draw = ImageDraw.Draw(img)
    
    # 1. LOGO: Üstte ve şık
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo.thumbnail((350, 350))
        img.paste(logo, (int((W - logo.size[0]) / 2), 150), logo)
    except: pass

    # 2. MESAJ
    draw.text((W/2, 500), "TAKİPTE KALIN", fill=(38, 166, 154), font=get_safe_font(70), anchor="mt")
    draw.multiline_text((W/2, 600), "Analizlerimizi kaçırmamak için\nbizi takip etmeyi unutmayın.", 
                        fill=txt_c, font=get_safe_font(45), align="center", anchor="mt")
    
    # 3. BUTON GÖRÜNÜMÜ
    draw.rounded_rectangle([340, 750, 740, 840], radius=45, fill=(38, 166, 154))
    draw.text((W/2, 770), "@finanszone", fill=(255, 255, 255), font=get_safe_font(40), anchor="mt")

    draw_pagination(draw, 4)
    return img

# --- 4. STREAMLIT ARAYÜZÜ ---
st.title("📱 FinansZone Carousel Botu")

metrics = get_pro_metrics()

if metrics:
    st.success("TCMB (EVDS) Verileri Başarıyla Alındı")
    col1, col2 = st.columns(2)
    col1.metric("Brüt Rezerv", metrics['rezerv'])
    col2.metric("TCMB Dolar", f"{metrics['dolar_tcmb']} TL")
else:
    st.error("EVDS verileri şu an çekilemiyor, lütfen API Key'i kontrol edin.")

if st.button("🚀 Karuseli Oluştur"):
    with st.spinner("Görseller Hazırlanıyor..."):
        # S3 ve S5 örneklerini gösteriyoruz (Diğerleri de benzer mantıkla eklenebilir)
        s3 = create_s3_evds(metrics, True)
        s5 = create_s5_final(True)
        
        st.image([s3, s5], caption=["Slayt 3 (EVDS)", "Slayt 5 (Kapanış)"], width=400)
        
        # İndirme Butonu Örneği
        buf = io.BytesIO()
        s5.save(buf, format="PNG")
        st.download_button("Son Slaytı İndir", buf.getvalue(), "kapanis.png", "image/png")

st.sidebar.caption("v2.1 - EVDS Entegreli")
