import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from config import settings

logger = logging.getLogger("EncryptionManager")


class EncryptionManager:
    """Uygulama genelinde kullanılan basit şifreleme yöneticisi."""

    def __init__(self, key: Optional[str] = None):
        self.key = self._resolve_key(key)
        self.cipher = Fernet(self.key)

    def _resolve_key(self, key: Optional[str]) -> bytes:
        if key:
            return key.encode() if isinstance(key, str) else key

        if settings.ENCRYPTION_KEY:
            return settings.ENCRYPTION_KEY.encode()

        generated_key = Fernet.generate_key()
        logger.warning(
            "ENCRYPTION_KEY bulunamadı, geçici bir anahtar oluşturuldu. "
            "Kalıcı şifre çözme için .env içine ENCRYPTION_KEY ekleyin."
        )
        return generated_key

    def encrypt(self, plain_text: str) -> str:
        if not plain_text:
            return ""
        try:
            return self.cipher.encrypt(str(plain_text).encode()).decode()
        except Exception as exc:
            logger.error(f"Şifreleme hatası: {exc}")
            return ""

    def decrypt(self, encrypted_text: str) -> str:
        if not encrypted_text:
            return ""
        try:
            return self.cipher.decrypt(str(encrypted_text).encode()).decode()
        except InvalidToken as exc:
            logger.error(f"Şifre çözme hatası (anahtar uyumsuz): {exc}")
            return encrypted_text
        except Exception as exc:
            logger.error(f"Şifre çözme hatası: {exc}")
            return encrypted_text


encryption_manager = EncryptionManager()