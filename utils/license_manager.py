import base64
import json
import os
from datetime import datetime
from cryptography.fernet import Fernet, InvalidToken
from utils.system_id import get_device_fingerprint

class LicenseManager:
    def __init__(self):
        # ✅ Düzeltildi: Secret key dosyadan okunuyor
        secret_key_path = os.path.join(os.path.dirname(__file__), '..', 'secret.key')
        
        try:
            # secret.key dosyasından oku
            if os.path.exists(secret_key_path):
                with open(secret_key_path, 'rb') as f:
                    self.secret_key = f.read().strip()
            else:
                # Dosya yoksa varsayılan (geçici)
                print("⚠️  secret.key bulunamadı, varsayılan kullanılıyor")
                self.secret_key = b'2lzmMcoZ2iIcLavAEX4wPX1HXlxRQzv3QzaLg7TCYk4='
            
            self.cipher = Fernet(self.secret_key)
        except Exception as e:
            print(f"⚠️  Lisans şifreleme hatası: {e}")
            self.cipher = None

    def validate_license(self, license_key_str: str):
        """
        Lisans doğrula
        Dönüş: (Geçerli_mi, Mesaj, Limit, Bitiş_Tarihi)
        """
        if not license_key_str:
            return False, "Lisans anahtarı girilmemiş.", 0, None

        if not self.cipher:
            return False, "Şifreleme hatası, secret.key kontrol edin.", 0, None

        try:
            # Şifreyi Çöz
            decoded_bytes = base64.urlsafe_b64decode(license_key_str.encode())
            decrypted_data = self.cipher.decrypt(decoded_bytes)
            data = json.loads(decrypted_data.decode())

            # 1. Tarih Kontrolü
            if data.get("expiry"):
                expiry_date = datetime.strptime(data["expiry"], "%Y-%m-%d")
                if datetime.now() > expiry_date:
                    return False, "Lisans süresi dolmuş!", 0, data["expiry"]

            # 2. Donanım Kilidi Kontrolü
            hw_id = get_device_fingerprint()
            if data.get("hw_id") and data.get("hw_id") != hw_id:
                return False, f"Bu lisans başka cihaza ait!\nBeklenen: {data.get('hw_id')}\nBu cihaz: {hw_id}", 0, None

            # 3. Lisans limiti
            limit = int(data.get("limit", 1))
            
            return True, "Lisans aktif ✅", limit, data.get("expiry")

        except InvalidToken:
            return False, "Geçersiz lisans anahtarı (şifre çözülemedi)!", 0, None
        except json.JSONDecodeError:
            return False, "Geçersiz lisans formatı!", 0, None
        except Exception as e:
            return False, f"Lisans doğrulama hatası: {str(e)}", 0, None