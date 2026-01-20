class SMSManager:
    def __init__(self, db):
        self.db = db
        # Gerçek entegrasyon için API bilgileri buraya gelir
        self.api_user = "demo"
        self.api_pass = "demo"

    def send_sms(self, phone, message):
        """
        SMS gönderir (Şimdilik sadece simülasyon).
        Eğer 'module_sms' kapalıysa göndermez.
        """
        # 1. Modül açık mı?
        if not self.db.is_module_active("module_sms"):
            print("SMS Modülü Kapalı. Gönderilmedi.")
            return False
        
        # 2. Telefon numarası temizliği
        if not phone: return False
        clean_phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # 3. API'ye İstek (Buraya gerçek kod gelecek)
        # Örn: requests.post("https://api.smsfirmasi.com/send", ...)
        
        print(f"📨 [SMS GÖNDERİLDİ] Kime: {clean_phone} | Mesaj: {message}")
        
        # 4. Logla
        self.db.log_action("Sistem", "SMS Gönderimi", f"{clean_phone} numarasına mesaj atıldı.")
        return True

    def send_appointment_reminder(self, patient_name, phone, date_str, time_str):
        msg = f"Sayin {patient_name}, {date_str} {time_str} tarihindeki randevunuzu hatirlatiriz. Lutfen gelmeden 15dk once hazir olunuz. - FIZYOMASTER"
        return self.send_sms(phone, msg)