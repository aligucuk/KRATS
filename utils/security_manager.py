import os
import logging
import hashlib
import bcrypt  # Şifreler için (Login)
from cryptography.fernet import Fernet # Veriler için (TC, Tel vb.)

# Loglama ayarı
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("SecurityManager")

class SecurityManager:
    def __init__(self):
        # 1. Veri Şifreleme Anahtarını Yükle (Fernet)
        self.key = self._load_key()
        try:
            self.cipher = Fernet(self.key)
        except Exception as e:
            logger.critical(f"Şifreleme anahtarı hatalı! Hata: {e}")
            raise e

    def _load_key(self):
        """
        Anahtarı yükleme önceliği: Environment -> Dosya -> Oluştur
        """
        # Ortam değişkeni
        env_key = os.getenv("CLINIC_APP_SECRET_KEY")
        if env_key:
            return env_key.encode()

        # Dosya kontrolü
        key_file = "secret.key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as file:
                return file.read()
        
        # Yoksa oluştur
        logger.warning("Anahtar bulunamadı. Yeni bir 'secret.key' oluşturuluyor.")
        key = Fernet.generate_key()
        with open(key_file, "wb") as file:
            file.write(key)
        return key

    # --- PASSWORD BÖLÜMÜ (BCRYPT - GÜVENLİ) ---
    
    def hash_password(self, password: str) -> str:
        """Şifreyi BCrypt ile güvenli hashler (Yavaş ve Tuzlu)"""
        if not password:
            raise ValueError("Password cannot be empty")
        try:
            # String -> Bytes
            password_bytes = password.encode('utf-8')
            # Salt + Hash
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            # Bytes -> String (Veritabanı için)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Hash hatası: {e}")
            raise RuntimeError(f"Password hashing failed: {e}") from e

    def verify_password(self, provided_password: str, stored_hash: str) -> bool:
        """Giriş şifresini doğrular"""
        if not provided_password or not stored_hash: return False
        try:
            # String -> Bytes
            password_bytes = provided_password.encode('utf-8')
            hash_bytes = stored_hash.encode('utf-8')
            # Kontrol et
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            logger.error(f"Doğrulama hatası: {e}")
            return False

    def validate_password_strength(self, password: str) -> tuple:
        if len(password) < 4:
            return False, "Şifre en az 4 karakter olmalı."
        return True, "Geçerli"

    # --- VERİ BÖLÜMÜ (FERNET - HASTA BİLGİLERİ İÇİN) ---

    def encrypt_data(self, plain_text):
        """Veriyi şifreler (TC, Tel, Adres vb.)"""
        if not plain_text:
            return ""  # Allow empty strings for optional fields
        try:
            # Fernet sadece bytes kabul eder
            return self.cipher.encrypt(str(plain_text).encode('utf-8')).decode('utf-8')
        except Exception as e:
            logger.error(f"Veri şifreleme hatası: {e}")
            raise RuntimeError(f"Data encryption failed: {e}") from e

    def decrypt_data(self, encrypted_text, strict=False):
        """Şifreli veriyi okur

        Args:
            encrypted_text: Şifreli metin
            strict: True ise hata durumunda exception fırlatır,
                   False ise (varsayılan) boş string döndürür
        """
        if not encrypted_text:
            return ""  # Allow empty strings for optional fields
        try:
            return self.cipher.decrypt(str(encrypted_text).encode('utf-8')).decode('utf-8')
        except Exception as e:
            # Şifre çözülemezse (eski anahtar vs.) logla
            logger.error(f"Veri çözme hatası: {e}")

            if strict:
                # Test/debug modunda exception fırlat
                raise RuntimeError(f"Data decryption failed: {e}") from e
            else:
                # Production'da backwards compatibility için warning ver ve boş dön
                logger.warning(f"Decryption failed, returning empty. Key mismatch suspected.")
                return ""  # Fallback for backwards compatibility