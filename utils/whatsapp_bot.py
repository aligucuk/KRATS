import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class WhatsAppBot:
    def __init__(self, db):
        self.db = db
        self.driver = None

    def start_bot(self):
        # DB Manager'dan randevuları çek
        apps = self.db.get_tomorrow_appointments()
        
        if not apps:
            print("📅 Yarına hatırlatılacak randevu yok.")
            return "Randevu bulunamadı."

        print("🚀 WhatsApp Bot Başlatılıyor...")
        
        try:
            options = webdriver.ChromeOptions()
            # options.add_argument("--headless") # QR okutmak için kapalı
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            self.driver.get("https://web.whatsapp.com")
            
            print("⚠️ Lütfen tarayıcıda QR Kodunu okutun.")
            
            # QR kod okunduktan sonra "sohbet listesi" elementinin gelmesini bekle (60sn)
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )
            print("✅ WhatsApp Web bağlandı!")

            count = 0
            for row in apps:
                # row yapısı: (id, decrypted_name, date, status, notes, decrypted_phone)
                # Not: get_tomorrow_appointments metodunun dönüşüne göre burayı ayarlıyoruz
                phone = row[5] # 5. indeks telefon (db_manager sorgusuna bak)
                name = row[1]  # 1. indeks isim
                date = row[2]  # 2. indeks tarih
                
                if self.send_message(phone, name, date):
                    count += 1
            
            return f"{count} kişiye mesaj gönderildi."

        except Exception as e:
            print(f"❌ Bot Hatası: {e}")
            return f"Bot Hatası: {str(e)}"
        finally:
            if self.driver:
                self.driver.quit()

    def send_message(self, phone, name, date):
        try:
            # Saat formatlama
            time_str = str(date)[11:16] # "2023-10-25 14:30" -> "14:30"

            msg = f"Merhaba Sayın {name}, yarın saat {time_str} randevunuzu hatırlatırız. Sağlıklı günler dileriz."
            
            # Telefon temizliği
            clean_phone = "".join(filter(str.isdigit, str(phone)))
            
            # Türkiye ise başına 90 ekle
            if len(clean_phone) == 10 and clean_phone.startswith("5"):
                clean_phone = "90" + clean_phone
            
            encoded_msg = urllib.parse.quote(msg)
            url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"
            
            self.driver.get(url)
            
            # "Gönder" butonunu bekle ve tıkla
            send_btn = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]'))
            )
            send_btn.click()
            
            time.sleep(3) # Gönderim için bekle
            print(f"📤 Gönderildi: {name}")
            return True

        except Exception as e:
            print(f"⚠️ Mesaj Gönderilemedi ({name}): {e}")
            return False