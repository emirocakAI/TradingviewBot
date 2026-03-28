import streamlit as st

st.set_page_config(page_title="FinansZone Tools Portal", layout="wide")

# Logo ve Başlık
col1, col2 = st.columns([1, 5])
with col1:
    try:
        st.image("finanszone 1.png", width=120)
    except:
        pass
with col2:
    st.title("FinansZone Profesyonel Araçlar Paneli")
    st.write("Projeler arasında geçiş yapmak için aşağıdaki kutucukları kullanın veya soldaki menüyü açın.")

st.divider()

# Proje Kutucukları (Kullanıcı dostu arayüz)
col_a, col_b = st.columns(2)

with col_a:
    st.info("### 📈 Tekli Hisse Raporlayıcı")
    st.write("TradingView üzerinden anlık verilerle jilet gibi hisse analiz görselleri oluşturun.")
    if st.button("Rapor Botuna Git →"):
        st.switch_page("pages/1_Rapor_Botu.py")

with col_b:
    st.success("### 🎠 Haftalık Carousel Oluşturucu")
    st.write("Haftalık piyasa karnesi, kazananlar ve kaybedenler için kaydırmalı post hazırlayın.")
    if st.button("Carousel Botuna Git →"):
        st.switch_page("pages/2_Carousel_Botu.py")

st.sidebar.success("Yukarıdan bir araç seçin.")
st.sidebar.markdown("---")
st.sidebar.write("FinansZone Yönetim Paneli")
