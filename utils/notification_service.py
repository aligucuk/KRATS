import threading
import time
import smtplib
import urllib.parse
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationService:
    def __init__(self, db):
        self.db = db
        self.is_running = False
        self.last_daily_check = None

    def start_daemon(self):
        """Servisi arka planda başlatır"""
        if not self.is_running:
            self.is_running = True
            threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        print("🔔 Bildirim Servisi Başlatıldı (Gelişmiş Mod)")
        while self.is_running:
            try:
                # 1. Bildirimleri Kontrol Et (Yarınki randevular)
                self.check_and_send()
                
                # 2. Günlük Bakım (Günde 1 kere)
                self.run_daily_tasks()

                # 1 Saat bekle (Test için 60sn yapabilirsin)
                time.sleep(3600) 
            except Exception as e:
                print(f"⚠️ Bildirim Servisi Hatası: {e}")
                time.sleep(60)

    def run_daily_tasks(self):
        """Günde sadece bir kez çalışacak rutinler"""
        now = datetime.now()
        if (self.last_daily_check is None or self.last_daily_check.day != now.day) and now.hour >= 9:
            print("📅 Günlük Rutin Kontrolü Yapılıyor...")
            self.last_daily_check = now

    def check_and_send(self):
        """Veritabanından yarınki randevuları çeker ve bildirim atar"""
        # SMS ve Email modülleri kapalıysa hiç yorma
        sms_active = self.db.is_module_active("module_sms")
        email_active = True # Email genelde açıktır veya ayarlara bağlanabilir

        if not sms_active and not email_active:
            return

        try:
            # db_manager.py içindeki metod
            pending = self.db.get_pending_reminders()
        except:
            return

        if not pending: return

        # Ayarlardan Şablonları Çek
        sms_template = self.db.get_setting("sms_template") or "Sayin {hasta}, yarin {saat} randevunuz vardir."
        email_template = self.db.get_setting("email_template") or "Sayin {hasta},\n\nYarin {tarih} saat {saat} randevunuzu hatirlatiriz.\n\nSaglikli Gunler."

        for app in pending:
            # app yapısı: (id, name, phone, email, date_str)
            app_id, p_name, p_phone, p_email, app_date_str = app
            
            # Tarih ayrıştırma
            try:
                dt = datetime.strptime(app_date_str, "%Y-%m-%d %H:%M")
                date_part = dt.strftime("%d.%m.%Y")
                time_part = dt.strftime("%H:%M")
            except:
                date_part = app_date_str
                time_part = ""

            # Mesajı Hazırla
            final_sms = sms_template.replace("{hasta}", p_name).replace("{tarih}", date_part).replace("{saat}", time_part)
            final_email_body = email_template.replace("{hasta}", p_name).replace("{tarih}", date_part).replace("{saat}", time_part)

            sent = False
            
            # 1. SMS Gönderimi
            if sms_active and p_phone:
                if self.simulate_sms(p_phone, final_sms):
                    sent = True

            # 2. Email Gönderimi
            if email_active and p_email and "@" in p_email:
                sender_mail = self.db.get_setting("api_email_user")
                sender_pass = self.db.get_setting("api_email_pass") # Düzeltme: Şifre alanı
                if sender_mail and sender_pass:
                    if self.send_smart_email(sender_mail, sender_pass, "Randevu Hatirlatmasi", p_email, final_email_body):
                        sent = True

            # Başarılıysa veritabanında işaretle
            if sent:
                self.db.mark_reminder_sent(app_id)

    def simulate_sms(self, phone, message):
        """Gerçek API olmadığı için terminale basar (Netgsm vb. buraya entegre edilir)"""
        print(f"📨 [SMS GÖNDERİLDİ] -> {phone} : {message}")
        return True

    def send_smart_email(self, sender_mail, sender_pass, subject, receiver_mail, body):
        """
        Gönderici mail adresinin uzantısına göre SMTP sunucusunu otomatik seçer.
        """
        try:
            smtp_server = "smtp.gmail.com" # Varsayılan
            smtp_port = 587
            domain = sender_mail.split("@")[-1].lower()

            if "gmail.com" in domain: smtp_server = "smtp.gmail.com"
            elif "icloud.com" in domain: smtp_server = "smtp.mail.me.com"
            elif "outlook.com" in domain or "hotmail.com" in domain: smtp_server = "smtp.office365.com"
            elif "yahoo.com" in domain: smtp_server = "smtp.mail.yahoo.com"
            elif "yandex.com" in domain:
                smtp_server = "smtp.yandex.com"
                smtp_port = 465

            msg = MIMEMultipart()
            msg['From'] = sender_mail
            msg['To'] = receiver_mail
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
            
            server.login(sender_mail, sender_pass)
            server.sendmail(sender_mail, receiver_mail, msg.as_string())
            server.quit()
            
            print(f"📧 [EMAIL GÖNDERİLDİ] -> {receiver_mail}")
            return True

        except Exception as e:
            print(f"❌ Mail Hatası: {e}")
            return False