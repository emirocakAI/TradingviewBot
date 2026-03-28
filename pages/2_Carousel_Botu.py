import streamlit as st
import pandas as pd
from evds import evdsAPI
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# --- 1. AYARLAR & API ---
EVDS_KEY = "8nTja3zQFQ" # Paylaştığın anahtar eklendi
evds = evdsAPI(EVDS_KEY)
FONT_PATH = "Outfit-VariableFont_wght.ttf"
LOGO_PATH = "finanszone 1.png"
W, H = 1080, 1080

# --- 2. EVDS VERİ ÇEKME FONKSİYONU ---
def get_evds_data():
    try:
        end_date = datetime.now().strftime('%d-%m-%Y')
        start_date = (datetime.now() - timedelta(days=15)).strftime('%d-%m-%Y')
        
        # TP.AB.G02: TCMB Brüt Döviz Rezervleri (Milyon Dolar)
        # TP.DK.USD.A.YTL: ABD Doları (Döviz Alış)
        df = evds.get_data(['TP.AB.G02', 'TP.DK.USD.A.YTL'], startdate=start_date, enddate=end_date)
        
        # Son iki geçerli veriyi kıyasla (Haftalık değişim için)
        df = df.dropna()
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        rezerv_degisim = latest['TP.AB.G02'] - prev['TP.AB.G02']
        usd_degisim = ((latest['TP.DK.USD.A.YTL'] - prev['TP.DK.USD.A.YTL']) / prev['TP.DK.USD.A.YTL']) * 100
        
        return {
            "TCMB Rezerv": f"{'+' if rezerv_degisim > 0 else ''}{round(rezerv_degisim/1000, 2)} Mlyr $",
            "Dolar/TL (TCMB)": f"{'+' if usd_degisim > 0 else ''}{round(usd_degisim, 2)}%",
            "Rezerv Durumu": latest['TP.AB.G02']
        }
    except Exception as e:
        return {"Hata": "Veri Çekilemedi", "Detay": str(e)}

# --- 3. DİNAMİK VERİ SAYFASI (S3 - EVDS ÖZEL) ---
def create_evds_slide(data, is_dark):
    bg_color = (19, 23, 34) if is_dark else (255, 255, 255)
    img = Image.new('RGB', (W, H), color=bg_color)
    draw = ImageDraw.Draw(img)
    txt_c = (255, 255, 255) if is_dark else (0, 0, 0)
    accent = (38, 166, 154)

    # Başlık
    draw.text((80, 80), "MERKEZ BANKASI ANALİZİ", fill=txt_c, font=ImageFont.truetype(FONT_PATH, 70))
    draw.rectangle([80, 170, 350, 180], fill=accent)

    # Veri Kutuları
    y = 250
    # Rezerv Göstergesi
    draw.rounded_rectangle([80, y, W-80, y+200], radius=25, fill=(30, 36, 50) if is_dark else (240, 242, 246))
    draw.text((120, y+40), "Haftalık Rezerv Değişimi", fill=(150, 150, 150), font=ImageFont.truetype(FONT_PATH, 40))
    val = data.get("TCMB Rezerv", "Veri Yok")
    c = accent if "+" in val else (255, 82, 82)
    draw.text((120, y+90), val, fill=c, font=ImageFont.truetype(FONT_PATH, 80))
    
    # Alt Mesaj (AI Yorumu gibi)
    y += 250
    note = "Merkez Bankası brüt rezervleri piyasa likiditesi\naçısından kritik eşikte seyrediyor."
    draw.multiline_text((80, y), note, fill=txt_c, font=ImageFont.truetype(FONT_PATH, 45), spacing=15)

    # Baloncuk (3. sayfa)
    # (Önceki draw_pagination_dots fonksiyonunu buraya entegre edebilirsin)
    return img

# --- 4. STREAMLIT ARAYÜZÜ ---
st.title("🛡️ FinansZone Pro: Haftalık Piyasa Karnesi")

if st.button("📈 Profesyonel Verileri Getir"):
    with st.spinner("TCMB Veritabanına bağlanılıyor..."):
        evds_results = get_evds_data()
        
        if "Hata" in evds_results:
            st.error(f"EVDS Hatası: {evds_results['Detay']}")
        else:
            st.success("TCMB Verileri Başarıyla Çekildi!")
            st.json(evds_results) # Kontrol için ekranda göster
            
            # Slaytı Oluştur
            pro_slide = create_evds_slide(evds_results, True)
            st.image(pro_slide, caption="TCMB Veri Slaytı", use_container_width=True)
