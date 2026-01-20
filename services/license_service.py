import hashlib
import platform
import subprocess
import os
from datetime import datetime
from typing import Dict, Optional

# Yapılandırma dosyasından ayarları çek
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

class LicenseService:
    def __init__(self):
        # Eğer config'den gelmezse varsayılan salt kullan
        self.secret_salt = settings.HARDWARE_ID_SALT or "KRATS_DEFAULT_SALT_2026"
        self.license_key_file = "license.key"

    def get_hardware_id(self) -> str:
        """
        Cihazın benzersiz donanım kimliğini (HWID) üretir.
        MAC Adresi + İşletim Sistemi bilgisini kullanır.
        """
        try:
            # İşletim sistemi bilgisi
            system_info = platform.system() + platform.release()
            
            # MAC Adresi (UUID modülü daha güvenilirdir)
            import uuid
            mac_addr = hex(uuid.getnode()).replace('0x', '').upper()
            
            # Ham veriyi birleştir
            raw_data = f"{mac_addr}-{system_info}-{self.secret_salt}"
            
            # SHA256 ile hashle
            hwid_hash = hashlib.sha256(raw_data.encode()).hexdigest().upper()
            
            # Okunabilir format: XXXX-XXXX-XXXX-XXXX
            formatted_hwid = '-'.join([hwid_hash[i:i+4] for i in range(0, 16, 4)])
            
            return formatted_hwid
        except Exception as e:
            logger.error(f"HWID oluşturma hatası: {e}")
            return "UNKNOWN-DEVICE-ID"

    def check_license(self) -> bool:
        """
        Lisansın geçerli olup olmadığını kontrol eder.
        """
        try:
            # 1. Kayıtlı lisans anahtarını dosyadan veya Config'den oku
            stored_key = self._load_license_key()
            
            if not stored_key:
                logger.warning("Lisans anahtarı bulunamadı.")
                return False
            
            # 2. Şu anki donanım için olması gereken anahtarı üret
            hwid = self.get_hardware_id()
            expected_key = self._generate_expected_key(hwid)
            
            # 3. Karşılaştır
            if stored_key == expected_key:
                return True
            else:
                logger.warning(f"Geçersiz lisans anahtarı! Beklenen: {expected_key}, Bulunan: {stored_key}")
                return False
                
        except Exception as e:
            logger.error(f"Lisans kontrol hatası: {e}")
            return False

    def activate_license(self, input_key: str) -> bool:
        """
        Girilen anahtarı doğrular ve geçerliyse kaydeder.
        """
        try:
            hwid = self.get_hardware_id()
            expected_key = self._generate_expected_key(hwid)
            
            # Boşlukları temizle
            clean_input_key = input_key.strip().upper()
            
            if clean_input_key == expected_key:
                self._save_license_key(clean_input_key)
                logger.info("Lisans başarıyla etkinleştirildi.")
                return True
            else:
                logger.warning("Lisans etkinleştirme başarısız: Anahtar hatalı.")
                return False
                
        except Exception as e:
            logger.error(f"Aktivasyon hatası: {e}")
            return False

    def get_license_info(self) -> Dict:
        """
        Lisans bilgilerini döndürür (Arayüzde göstermek için).
        """
        is_valid = self.check_license()
        return {
            "status": "Aktif" if is_valid else "Lisanssız",
            "hardware_id": self.get_hardware_id(),
            "license_type": "Pro" if is_valid else "Deneme",
            "user_limit": "Sınırsız" if is_valid else "1"
        }

    # --- YARDIMCI METOTLAR (Private) ---

    def _generate_expected_key(self, hwid: str) -> str:
        """
        Bir HWID için geçerli olması gereken lisans anahtarını üretir.
        Mantık: SHA256(HWID + SECRET_KEY) -> İlk 16 karakter
        """
        # Config'deki gizli anahtarı kullan (yoksa varsayılan)
        secret = settings.LICENSE_SECRET_KEY or "SUPER_SECRET_KEY_99"
        
        raw = f"{hwid}|{secret}"
        hashed = hashlib.sha256(raw.encode()).hexdigest().upper()
        
        # XXXX-XXXX-XXXX-XXXX formatında
        return '-'.join([hashed[i:i+4] for i in range(0, 16, 4)])

    def _load_license_key(self) -> Optional[str]:
        """Kayıtlı lisans anahtarını dosyadan okur."""
        if os.path.exists(self.license_key_file):
            try:
                with open(self.license_key_file, "r") as f:
                    return f.read().strip()
            except:
                return None
        return None

    def _save_license_key(self, key: str):
        """Lisans anahtarını dosyaya kaydeder."""
        try:
            with open(self.license_key_file, "w") as f:
                f.write(key)
        except Exception as e:
            logger.error(f"Lisans dosyası yazma hatası: {e}")