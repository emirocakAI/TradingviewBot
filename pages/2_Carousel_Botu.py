import streamlit as st
import yfinance as yf
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import os

# --- 1. AYARLAR ---
FONT_PATH = "Outfit-VariableFont_wght.ttf"
LOGO_PATH = "finanszone 1.png"

# --- 2. VERİ ÇEKME ---
def get_market_data():
    symbols = {"BIST 100": "XU100.IS", "USD/TRY": "USDTRY=X", "Gram Altın": "GC=F", "BIST Banka": "XBANK.IS"}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    results = {}
    for name, ticker in symbols.items():
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if len(df) >= 2:
                # Kapanış ve Açılış değerleri ile haftalık % değişim
                open_p = float(df['Open'].iloc[0])
                close_p = float(df['Close'].iloc[-1])
                change = ((close_p - open_p) / open_p) * 100
                results[name] = f"{'+' if change > 0 else ''}{round(change, 2)}%"
            else:
                results[name] = "N/A"
        except:
            results[name] = "Hata"
    return results

# --- 3. AI MANŞET MOTORU (Dinamik Analiz) ---
def generate_ai_headline(data):
    try:
        bist_change = float(data.get("BIST 100", "0%").replace("%", ""))
        usd_change = float(data.get("USD/TRY", "0%").replace("%", ""))
        
        # BIST analizi
        if bist_change > 1.5:
            bist_status = "BIST-100 haftayı güçlü bir yükselişle kapattı."
        elif bist_change < -1.5:
            bist_status = "Borsada bu hafta satış baskısı hakimdi."
        else:
            bist_status = "Piyasalarda bu hafta yatay bir seyir izlendi."
            
        # Döviz analizi
        if usd_change > 0.5:
            curr_status = "Döviz kurlarında yukarı yönlü hareket hızlandı."
        else:
            curr_status = "Küresel piyasalarda veri akışı takibimizdeydi."
            
        return f"{bist_status}\n{curr_status}"
    except:
        return "Haftalık piyasa verileri ve kritik\ngelişmeler analiz edildi."

# --- 4. KAPAK TASARIMI (Hizalamalar ve Tarih Düzeltildi) ---
def create_cover_slide(date_range, headline, is_dark=True):
    # 1080x1080 Kare Format
    w, h = 1080, 1080
    bg_color = (19, 23, 34) if is_dark else (255, 255, 255)
    # Rakamlar black (siyah) olarak istendi, bu yüzden txt_color her zaman siyah olacak
    txt_color = (0, 0, 0) if not is_dark else (255, 255, 255) # Temaya göre genel metin rengi
    # Değerlerin rengi kaldırıldı, sadece tek bir txt_color (black/white) kullanılacak.

    accent_color = (38, 166, 154) # Vurgu rengi
    
    img = Image.new('RGB', (w, h), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Fontlar
    f_title = ImageFont.truetype(FONT_PATH, 100)
    f_date = ImageFont.truetype(FONT_PATH, 42)
    f_headline = ImageFont.truetype(FONT_PATH, 55)
    f_dots = ImageFont.truetype(FONT_PATH, 50) # Boncuk fontu

    # 1. LOGO (Tam Merkezi)
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_w = 400
        logo_h = int(logo.size[1] * (logo_w / logo.size[0]))
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
        # Logoyu tam merkeze yapıştır (x: (w-lw)/2, y: 120)
        img.paste(logo, (int((w - logo_w) / 2), 120), logo)
        start_y = 120 + logo_h + 80
    except:
        start_y = 300

    # 2. BAŞLIK (Tam Merkezi Hizalama)
    title_text = "HAFTALIK PİYASA KARNESİ"
    # bbox hesabı ile metni tam ortala
    t_bbox = draw.textbbox((0, 0), title_text, font=f_title)
    draw.text(((w - (t_bbox[2]-t_bbox[0]))/2, start_y), title_text, fill=txt_color, font=f_title)
    
    # 3. TARİH (Tam Merkezi, Format Düzeltildi: 28.03.2026)
    # Tarih formatı 28.03.2026 olarak st.text_input'dan geliyor.
    date_text = f"Tarih: {date_range}"
    d_bbox = draw.textbbox((0, 0), date_text, font=f_date)
    draw.text(((w - (d_bbox[2]-d_bbox[0]))/2, start_y + 120), date_text, fill=(130, 130, 130), font=f_date)

    # 4. MANŞET (Sol Kenara Yaslı, Şık Kutu İçinde)
    # Manşet Alanı - Alt Kısım
    margin = 80
    draw.rectangle([margin, 700, margin + 250, 712], fill=accent_color) # Yeşil ayraç
    # align="left" ve spacing=15 ile sola yaslı manşet
    draw.multiline_text((margin, 740), headline, fill=txt_color, font=f_headline, spacing=15, align="left")
    
    # 5. BONCUKLAR (Tam Merkezi, Sembol Düzeltildi)
    # Hata: unicode karakter hatası. Yaygın desteklenen • ve ◦ sembolleri kullanıldı.
    dots_text = "• ◦ ◦ ◦ ◦" # Sayfa 1: Kapak
    dots_bbox = draw.textbbox((0, 0), dots_text, font=f_dots)
    # Alttaki konumu düzeltildi (h - 100).
    draw.text(((w - (dots_bbox[2]-dots_bbox[0]))/2, h - 100), dots_text, fill=accent_color, font=f_dots)
    
    # Benzersiz dosya adı
    path = f"cover_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(path)
    return path

# --- 5. SLAYT 2: PİYASA VERİLERİ (Rakamlar Black/White Olarak Güncellendi) ---
def create_data_slide(market_data, is_dark=True):
    w, h = 1080, 1080
    bg_color = (19, 23, 34) if is_dark else (255, 255, 255)
    # Rakamlar black (siyah) olarak istendi, bu yüzden txt_color her zaman siyah olacak
    # Aydınlık temada metin siyah, karanlık temada beyaz olacak.
    txt_color = (0, 0, 0) if not is_dark else (255, 255, 255)
    
    # Kart arka planı daha belirginleştirildi
    card_bg = (30, 36, 50) if is_dark else (240, 242, 246)
    accent_color = (38, 166, 154) # Vurgu rengi
    
    img = Image.new('RGB', (w, h), color=bg_color)
    draw = ImageDraw.Draw(img)
    f_header, f_label, f_value, f_dots = ImageFont.truetype(FONT_PATH, 75), ImageFont.truetype(FONT_PATH, 48), ImageFont.truetype(FONT_PATH, 65), ImageFont.truetype(FONT_PATH, 50)

    # 1. Başlık (Tam Merkezi)
    header_text = "PİYASA PERFORMANSI"
    header_bbox = draw.textbbox((0, 0), header_text, font=f_header)
    draw.text(((w - (header_bbox[2]-header_bbox[0]))/2, 80), header_text, fill=txt_color, font=f_header)
    # Alt çizgi vurgusu
    draw.rectangle([80, 175, 300, 185], fill=accent_color)

    # 2. Veri Kartlarını Oluştur
    start_y, card_h, spacing = 250, 160, 30
    # market_data Örn: {'BIST 100': '-1.21%', 'USD/TRY': '+0.35%', ...}
    
    for i, (label, value) in enumerate(market_data.items()):
        curr_y = start_y + (i * (card_h + spacing))
        
        # Kart Arka Planı (Yuvarlatılmış Köşeli)
        draw.rounded_rectangle([80, curr_y, w - 80, curr_y + card_h], radius=20, fill=card_bg)
        
        # Etiket (Sol Taraf)
        draw.text((130, curr_y + 50), label, fill=(180, 180, 180), font=f_label)
        
        # Değer (Sağ Taraf, Renk Kaldırıldı, Siyah/Beyaz)
        # Değeri sağa yaslamak için bbox hesabı
        v_bbox = draw.textbbox((0, 0), value, font=f_value)
        v_w = v_bbox[2] - v_bbox[0]
        # Renk kontrolü (accent_color/loss_color) kaldırıldı, tüm metin ve değerler tek bir txt_color (black/white) ile yazıldı.
        draw.text((w - v_w - 130, curr_y + 42), value, fill=txt_color, font=f_value)

    # 3. BONCUKLAR (Sayfa 2: ○ ● ○ ○ ○ -> Düzeltildi)
    # Sayfa 2: ○ ● ○ ○ ○ -> Düzeltildi (Standard Unicode • and ◦ used for compatibility)
    dots_text = "◦ • ◦ ◦ ◦" # Sayfa 2
    dots_bbox = draw.textbbox((0, 0), dots_text, font=f_dots)
    # Alttaki konumu düzeltildi (h - 100).
    draw.text(((w - (dots_bbox[2]-dots_bbox[0]))/2, h - 100), dots_text, fill=accent_color, font=f_dots)
    
    path = f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(path)
    return path

# --- 6. STREAMLIT UI ---
st.set_page_config(page_title="FinansZone Carousel", layout="wide")
if "carousel_history" not in st.session_state: st.session_state.carousel_history = []

col_logo, col_title = st.columns([1, 6])
with col_logo:
    try: st.image(LOGO_PATH, width=100)
    except: pass
with col_title:
    st.title("Carousel Oluşturucu")

with st.sidebar:
    st.header("⚙️ Kontrol Paneli")
    # Tarih formatı 28.03.2026 olarak güncellendi (strftime ile)
    date_input = st.text_input("Tarih Aralığı", value=datetime.now().strftime("%d.%m.%Y"))
    st.info("Manşet, verilere göre otomatik oluşturulacaktır.")
    theme = st.radio("Tema", ["Karanlık", "Aydınlık"])
    if st.button("🗑️ Geçmişi Temizle"):
        st.session_state.carousel_history = []
        st.rerun()

if st.button("🚀 Carousel Paketini Hazırla"):
    with st.spinner("Piyasa taranıyor ve analiz ediliyor..."):
        # 1. Verileri Çek
        data = get_market_data()
        
        # 2. AI Manşeti oluştur
        auto_headline = generate_ai_headline(data)
        
        # 3. Slayt 1 (Kapak) ve Slayt 2 (Data) oluştur
        slide1_path = create_cover_slide(date_input, auto_headline, theme == "Karanlık")
        slide2_path = create_data_slide(data, theme == "Karanlık")
        
        # Hafızaya kaydet (Sohbet Akışı için)
        st.session_state.carousel_history.insert(0, {
            "pages": [slide1_path, slide2_path],
            "date": date_input,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        st.rerun()

# --- GÖSTERİM DÖNGÜSÜ ---
st.divider()
for entry in st.session_state.carousel_history:
    with st.container():
        # Başlık ve Tarih (Streamlit UI'da)
        st.subheader(f"📊 {entry['date']} Karnesi ({entry['timestamp']})")
        
        # Carousel Boncukları ve Aktif Sayfa Bilgisi (Streamlit UI'da)
        # i=0 ise en son oluşturulan, i=1 ise bir önceki
        # Bu bilgi görselin içinde zaten var (Boncuk 1 aktif), burada sadece UI'da teyit ediyoruz.
        # i=0 Kapak (Slide 1), i=1 Data (Slide 2)
        st.caption(f"Carousel Sayfa {1 if entry['pages'][0] == entry['pages'][0] else 2} / 5 (Kapak)")
        
        cols = st.columns(len(entry['pages']))
        for i, p_path in enumerate(entry['pages']):
            with cols[i]:
                # Görseli göster ve indirme butonu koy
                st.image(p_path, use_container_width=True, caption=f"Sayfa {i+1}")
                with open(p_path, "rb") as f:
                    st.download_button(f"📥 Sayfa {i+1} İndir", f, f"Slayt_{i+1}.png", key=p_path)
        st.divider()
