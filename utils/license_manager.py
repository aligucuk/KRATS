import base64
import json
from datetime import datetime
from cryptography.fernet import Fernet, InvalidToken
from utils.system_id import get_device_fingerprint

class LicenseManager:
    def __init__(self):
        # BU SENİN GİZLİ ANAHTARIN (Değiştirme, keygen ile aynı olmalı)
        self.secret_key = b'xMedFoOkNJp2Mk4r34AXvTmpx7u34GkyjdgGYFwGfBc=' 
        try:
            self.cipher = Fernet(self.secret_key)
        except: pass

    def validate_license(self, license_key_str: str):
        """Dönüş: (Geçerli_mi, Mesaj, Limit, Bitiş_Tarihi)"""
        if not license_key_str:
            return False, "Lisans anahtarı girilmemiş.", 0, None # LİMİT 0

        try:
            # Şifreyi Çöz
            decoded_bytes = base64.urlsafe_b64decode(license_key_str.encode())
            decrypted_data = self.cipher.decrypt(decoded_bytes)
            data = json.loads(decrypted_data.decode())

            # 1. Tarih Kontrolü
            if data.get("expiry"):
                if datetime.now() > datetime.strptime(data["expiry"], "%Y-%m-%d"):
                    return False, "Süre doldu!", 0, data["expiry"]

            # 2. Donanım Kilidi Kontrolü
            hw_id = get_device_fingerprint()
            if data.get("hw_id") and data.get("hw_id") != hw_id:
                return False, "Bu lisans başka bilgisayara ait!", 0, None

            return True, "Aktif", int(data.get("limit", 1)), data.get("expiry")

        except:
            return False, "Geçersiz Anahtar!", 0, None