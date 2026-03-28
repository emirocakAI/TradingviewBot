import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from PIL import Image
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="FinansZone Bot", layout="wide")

# --- LAZY IMPORT & DATA FUNCTION ---
@st.cache_data(ttl=3600)  # Verileri 1 saat önbelleğe alır, hızı artırır
def get_evds_indicators(api_key):
    try:
        # Kütüphaneyi burada içe aktararak açılış çakışmasını önlüyoruz
        from evds import evdsAPI
        evds = evdsAPI(api_key)
        
        # Tarih aralığını geniş tutuyoruz (Hafta sonu boşluğunu aşmak için)
        end_date = datetime.now().strftime('%d-%m-%Y')
        start_date = (datetime.now() - timedelta(days=20)).strftime('%d-%m-%Y')
        
        # TCMB Veri Serileri: Brüt Rezerv ve Dolar Kuru
        seriler = ['TP.AB.G02', 'TP.DK.USD.A.YTL']
        df = evds.get_data(seriler, startdate=start_date, enddate=end_date)
        
        # Veri temizliği
        df = df.dropna().reset_index(drop=True)
        
        if df.empty:
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        rezerv = latest['TP.AB.G02']
        rezerv_fark = rezerv - prev['TP.AB.G02']
        usd_kur = latest['TP.DK.USD.A.YTL']
        
        return {
            "rezerv": f"{round(rezerv/1000, 2)} Mlyr $",
            "rezerv_degisim": f"{round(rezerv_fark/1000, 2)} Mlyr $",
            "usd": f"{round(usd_kur, 4)} TL"
        }
    except Exception as e:
        print(f"EVDS Hatası: {e}")
        return None

# --- ANA EKRAN ---
st.title("📊 FinansZone Grafik & Veri Paneli")

# Sidebar - API Anahtarı Kontrolü
with st.sidebar:
    st.header("Ayarlar")
    evds_key = st.text_input("EVDS API Anahtarı", value="8nTja3zQFQ", type="password")
    st.divider()
    st.info("Uygulama başlatıldı. Veriler yükleniyor...")

# Üst Bilgi Kartları (Metrics)
col1, col2, col3 = st.columns(3)

evds_data = get_evds_indicators(evds_key)

if evds_data:
    col1.metric("TCMB Brüt Rezerv", evds_data["rezerv"], evds_data["rezerv_degisim"])
    col2.metric("TCMB Dolar Kuru", evds_data["usd"])
else:
    col1.warning("Rezerv verisi şu an alınamadı.")
    col2.info("Dolar (TCMB) bekleniyor...")

# Yfinance ile Canlı Piyasa Verisi (Örnek: BIST 100)
try:
    bist = yf.Ticker("XU100.IS")
    bist_last = bist.history(period="1d")['Close'].iloc[-1]
    col3.metric("BIST 100", f"{round(bist_last, 2)}")
except:
    col3.error("Piyasa verisi alınamadı.")

st.divider()

# --- GRAFİK OLUŞTURMA ALANI
