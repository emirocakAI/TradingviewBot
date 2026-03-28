def get_evds_data():
    try:
        # Aralığı 20 güne çıkarıyoruz ki hafta sonlarına takılmasın
        end_date = datetime.now().strftime('%d-%m-%Y')
        start_date = (datetime.now() - timedelta(days=20)).strftime('%d-%m-%Y')
        
        # Veriyi çek
        df = evds.get_data(['TP.AB.G02', 'TP.DK.USD.A.YTL'], startdate=start_date, enddate=end_date)
        
        # Boş satırları sil
        df = df.dropna()
        
        # KRİTİK KONTROL: Eğer tablo boşsa hata fırlatma, uyar!
        if df.empty:
            return {"Hata": "Veri Boş", "Detay": "Seçilen tarih aralığında TCMB verisi bulunamadı."}
        
        # En az 2 satır veri var mı kontrolü (Değişim hesaplamak için)
        if len(df) < 2:
            latest = df.iloc[-1]
            return {
                "TCMB Rezerv": f"{round(latest['TP.AB.G02']/1000, 2)} Mlyr $",
                "Dolar/TL (TCMB)": f"{latest['TP.DK.USD.A.YTL']}",
                "Not": "Haftalık değişim için yeterli veri yok."
            }

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
        return {"Hata": "Sistemsel Hata", "Detay": str(e)}
