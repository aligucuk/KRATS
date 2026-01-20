import hashlib
import os
import logging
from cryptography.fernet import Fernet

# Loglama ayarı
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("SecurityManager")

class SecurityManager:
    def __init__(self):
        self.key = self._load_key()
        try:
            self.cipher = Fernet(self.key)
        except Exception as e:
            logger.critical(f"Şifreleme anahtarı hatalı formatta! Uygulama çalışmayabilir. Hata: {e}")
            raise e

    def _load_key(self):
        """
        Anahtarı yükleme önceliği:
        1. Environment Variable (CLINIC_APP_SECRET_KEY)
        2. Yerel 'secret.key' dosyası
        3. Yeniden oluşturma
        """
        # 1. Ortam Değişkeni Kontrolü
        env_key = os.getenv("CLINIC_APP_SECRET_KEY")
        if env_key:
            return env_key.encode()

        # 2. Dosya Kontrolü
        key_file = "secret.key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as file:
                return file.read()
        
        # 3. Yeni Anahtar Oluşturma
        logger.warning("Anahtar bulunamadı. Yeni bir 'secret.key' oluşturuluyor.")
        key = Fernet.generate_key()
        with open(key_file, "wb") as file:
            file.write(key)
        return key

    # --- EKSİK OLAN HASH METODLARI (Login Hatası İçin) ---
    def hash_password(self, password):
        """Şifreyi SHA256 ile hashler (Geri döndürülemez)"""
        if not password: return ""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, stored_hash, provided_password):
        """Girilen şifre doğru mu kontrol eder"""
        if not provided_password or not stored_hash: return False
        current_hash = hashlib.sha256(provided_password.encode()).hexdigest()
        return current_hash == stored_hash

    # --- VERİ ŞİFRELEME (db_manager ile uyumlu isimler) ---
    def encrypt_data(self, plain_text):
        """Veriyi şifreler (db_manager 'encrypt_data' olarak çağırıyor)"""
        if not plain_text: return ""
        try:
            return self.cipher.encrypt(str(plain_text).encode()).decode()
        except Exception as e:
            logger.error(f"Şifreleme hatası: {e}")
            return ""

    def decrypt_data(self, encrypted_text):
        """Şifreyi çözer (db_manager 'decrypt_data' olarak çağırıyor)"""
        if not encrypted_text: return ""
        try:
            return self.cipher.decrypt(str(encrypted_text).encode()).decode()
        except Exception as e:
            # Hata durumunda (eski veri veya bozuk veri) ham halini dön
            logger.error(f"Şifre çözme hatası: {e}")
            return encrypted_text