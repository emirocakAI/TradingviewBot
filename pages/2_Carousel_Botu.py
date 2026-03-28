import streamlit as st
import yfinance as yf
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# --- 1. VERİ MOTORU (Haftalık Değişimleri Hesaplar) ---
def get_market_data():
    # Semboller: BIST100, Dolar, Altın, Bankacılık
    symbols = {
        "BIST 100": "XU100.IS",
        "USD/TRY": "USDTRY=X",
        "Gram Altın": "GC=F", # Ons üzerinden gram hesabı yapılabilir veya direkt sembol
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
            else:
                results[name] = "N/A"
        except:
            results[name] = "Error"
    return results

# --- 2. KAPAK TASARIMCISI (Slayt 1) ---
def create_cover_slide(date_range, is_dark=True):
    # 1080x1080 Kare Format
    w, h = 1080, 1080
    bg_color = (19, 23, 34) if is_dark else (255, 255, 255)
    txt_color = (255, 255, 255) if is_dark else (0, 0, 0)
    accent_color = (38, 166, 154) # FinansZone Yeşil Vurgusu
    
    img = Image.new('RGB', (w, h), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Fontlar
    try:
        f_title = ImageFont.truetype("Outfit-VariableFont_wght.ttf", 90) # Extra Bold
        f_date = ImageFont.truetype("Outfit-VariableFont_wght.ttf", 45)
        f_footer = ImageFont.truetype("Outfit-VariableFont_wght.ttf", 35)
    except:
        f_title = f_date = f_footer = ImageFont.load_default()

    # 1. Logo Ekleme (Sağ Üst)
    try:
        logo = Image.open("finanszone 1.png").convert("RGBA")
        logo.thumbnail((150, 150))
        img.paste(logo, (w - logo.width - 50, 50), logo)
    except: pass

    # 2. Ana Başlık (Orta)
    title_text = "HAFTALIK\nPİYASA\nKARNESİ"
    draw.multiline_text((80, 300), title_text, fill=txt_color, font=f_title, spacing=20)
    
    # 3. Vurgu Çizgisi
    draw.rectangle([80, 680, 300, 695], fill=accent_color)
    
    # 4. Tarih Aralığı
    draw.text((80, 730), f"Tarih: {date_range}", fill=(135, 135, 135), font=f_date)
    
    # 5. Alt Bilgi (İmza Yok, Sadece Marka)
    draw.text((80, h - 100), "finans.zone | Haftalık Analiz Raporu", fill=(135, 135, 135), font=f_footer)
    
    return img

# --- 3. STREAMLIT ARAYÜZÜ ---
st.set_page_config(page_title="FinansZone Carousel", layout="wide")
st.title("🎠 Haftalık Karne Carousel Oluşturucu")

with st.sidebar:
    st.header("⚙️ Ayarlar")
    date_input = st.text_input("Tarih Aralığı", value="18 - 22 Mart 2024")
    theme = st.radio("Tema", ["Karanlık", "Aydınlık"])
    dark_mode = theme == "Karanlık"
    
    st.markdown("---")
    st.info("Bu araç Carousel formatında 1080x1080 görseller üretir.")

if st.button("🚀 Carousel Hazırla"):
    # Verileri Çek
    data = get_market_data()
    
    # 1. Slaytı Oluştur (Kapak)
    cover_img = create_cover_slide(date_input, dark_mode)
    
    # Ekranda Göster
    st.subheader("1. Slayt: Kapak")
    st.image(cover_img, width=500)
    
    # İndirme Butonu
    cover_img.save("kapak.png")
    with open("kapak.png", "rb") as f:
        st.download_button("📥 Kapak Sayfasını İndir", f, "FinansZone_Kapak.png", "image/png")
