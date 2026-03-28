import streamlit as st
import yfinance as yf
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# --- 1. AYARLAR ---
FONT_PATH = "Outfit-VariableFont_wght.ttf"
LOGO_PATH = "finanszone 1.png"
W, H = 1080, 1080
ACCENT_COLOR = (38, 166, 154) # Yeşil
DOWN_COLOR = (255, 82, 82)    # Kırmızı

# --- 2. YARDIMCI FONKSİYONLAR ---
def get_safe_font(size):
    try: return ImageFont.truetype(FONT_PATH, size)
    except: return ImageFont.load_default()

def draw_pagination_dots(draw, current_page, total_pages=5):
    dot_radius = 7
    spacing = 30
    total_width = (total_pages - 1) * spacing
    start_x = (W - total_width) / 2
    y = H - 50 
    for i in range(total_pages):
        x = start_x + (i * spacing)
        if i == current_page:
            draw.ellipse([x-dot_radius, y-dot_radius, x+dot_radius, y+dot_radius], fill=ACCENT_COLOR)
        else:
            draw.ellipse([x-dot_radius, y-dot_radius, x+dot_radius, y+dot_radius], outline=ACCENT_COLOR, width=2)

def create_base_slide(is_dark):
    bg = (19, 23, 34) if is_dark else (255, 255, 255)
    img = Image.new('RGB', (W, H), color=bg)
    return img, ImageDraw.Draw(img), (255, 255, 255) if is_dark else (0, 0, 0)

# --- 3. SAYFA OLUŞTURUCULAR ---

# S1: KAPAK
def create_s1(date_range, headline, is_dark):
    img, draw, txt_c = create_base_slide(is_dark)
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA").resize((350, 100), Image.LANCZOS)
        img.paste(logo, (int((W-350)/2), 150), logo)
    except: pass
    
    draw.text(((W-draw.textbbox((0,0),"HAFTALIK PİYASA KARNESİ",font=get_safe_font(80))[2])/2, 350), "HAFTALIK PİYASA KARNESİ", fill=txt_c, font=get_safe_font(80))
    draw.text(((W-draw.textbbox((0,0),f"Tarih: {date_range}",font=get_safe_font(40))[2])/2, 450), f"Tarih: {date_range}", fill=(130,130,130), font=get_safe_font(40))
    
    draw.rectangle([120, 700, 370, 710], fill=ACCENT_COLOR)
    draw.multiline_text((120, 740), headline, fill=txt_c, font=get_safe_font(50), spacing=15)
    draw_pagination_dots(draw, 0)
    return img

# S2: PİYASA VERİLERİ
def create_s2(data, is_dark):
    img, draw, txt_c = create_base_slide(is_dark)
    draw.text((80, 80), "PİYASA PERFORMANSI", fill=txt_c, font=get_safe_font(70))
    draw.rectangle([80, 170, 300, 180], fill=ACCENT_COLOR)
    
    y = 220
    for label, val in data.items():
        draw.rounded_rectangle([80, y, W-80, y+150], radius=20, fill=(30,36,50) if is_dark else (240,242,246))
        draw.text((120, y+45), label, fill=(180,180,180), font=get_safe_font(45))
        c = ACCENT_COLOR if "+" in val else DOWN_COLOR
        v_w = draw.textbbox((0,0), val, font=get_safe_font(65))[2]
        draw.text((W-v_w-120, y+35), val, fill=c, font=get_safe_font(65))
        y += 180
    draw_pagination_dots(draw, 1)
    return img

# S3: HAFTANIN ENLERİ (AI Çıkarımı)
def create_s3(is_dark):
    img, draw, txt_c = create_base_slide(is_dark)
    draw.text((80, 80), "HAFTANIN ENLERİ", fill=txt_c, font=get_safe_font(70))
    draw.rectangle([80, 170, 300, 180], fill=ACCENT_COLOR)
    
    items = [("En Çok Yükselen", "BIST Banka", "+%4.2"), ("En Çok Düşen", "Havacılık", "-%2.1"), ("Haftanın Yıldızı", "Gram Altın", "Rekor")]
    y = 250
    for tit, name, val in items:
        draw.text((80, y), tit, fill=ACCENT_COLOR, font=get_safe_font(40))
        draw.text((80, y+50), name, fill=txt_c, font=get_safe_font(60))
        draw.text((W-250, y+50), val, fill=txt_c, font=get_safe_font(55))
        draw.line([80, y+130, W-80, y+130], fill=(60,60,60), width=2)
        y += 200
    draw_pagination_dots(draw, 2)
    return img

# S4: KRİTİK EŞİKLER
def create_s4(is_dark):
    img, draw, txt_c = create_base_slide(is_dark)
    draw.text((80, 80), "KRİTİK EŞİKLER", fill=txt_c, font=get_safe_font(70))
    draw.rectangle([80, 170, 300, 180], fill=ACCENT_COLOR)
    
    levels = [("BIST 100", "9.200", "9.800"), ("Dolar/TL", "32.10", "33.50"), ("Ons Altın", "2.150", "2.300")]
    y = 280
    draw.text((450, 220), "DESTEK", fill=(130,130,130), font=get_safe_font(35))
    draw.text((750, 220), "DİRENÇ", fill=(130,130,130), font=get_safe_font(35))
    
    for inst, sup, res in levels:
        draw.text((80, y), inst, fill=txt_c, font=get_safe_font(50))
        draw.text((450, y), sup, fill=DOWN_COLOR, font=get_safe_font(50))
        draw.text((750, y), res, fill=ACCENT_COLOR, font=get_safe_font(50))
        y += 120
    draw_pagination_dots(draw, 3)
    return img

# S5: KAPANIŞ
def create_s5(is_dark):
    img, draw, txt_c = create_base_slide(is_dark)
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA").resize((450, 130), Image.LANCZOS)
        img.paste(logo, (int((W-450)/2), 300), logo)
    except: pass
    
    msg = "Piyasa nabzını tutmak için\nbizi takipte kalın."
    m_w = draw.textbbox((0,0), "Piyasa nabzını tutmak için", font=get_safe_font(55))[2]
    draw.multiline_text(((W-m_w)/2, 500), msg, fill=txt_c, font=get_safe_font(55), align="center", spacing=20)
    
    draw.rounded_rectangle([340, 700, 740, 800], radius=50, fill=ACCENT_COLOR)
    draw.text((415, 725), "@finanszone", fill=(255,255,255), font=get_safe_font(45))
    draw_pagination_dots(draw, 4)
    return img

# --- 4. STREAMLIT ANA AKIŞ ---
st.set_page_config(page_title="FinansZone Mega Carousel", layout="wide")
st.title("🚀 FinansZone 5'li Karusel Paketi")

with st.sidebar:
    date_val = st.text_input("Tarih", datetime.now().strftime("%d.%m.%Y"))
    dark_mode = st.toggle("Karanlık Tema", True)

if st.button("🔥 Tüm Karuseli Oluştur"):
    data = {"BIST 100": "+1.24%", "USD/TRY": "+0.45%", "Gram Altın": "+2.10%", "BIST Banka": "-1.15%"} # Örnek
    headline = "Borsada Rekor Seviyeler Test Edildi.\nKüresel Piyasalarda Gözler Fed'de."
    
    slides = [
        create_s1(date_val, headline, dark_mode),
        create_s2(data, dark_mode),
        create_s3(dark_mode),
        create_s4(dark_mode),
        create_s5(dark_mode)
    ]
    
    cols = st.columns(5)
    for i, s_img in enumerate(slides):
        path = f"slide_{i+1}.png"
        s_img.save(path)
        with cols[i]:
            st.image(path, caption=f"Sayfa {i+1}")
            with open(path, "rb") as f:
                st.download_button(f"S{i+1} İndir", f, file_name=path)
