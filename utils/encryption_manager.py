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
            return ""  # Allow empty strings for optional fields
        try:
            return self.cipher.encrypt(str(plain_text).encode()).decode()
        except Exception as exc:
            logger.error(f"Şifreleme hatası: {exc}")
            raise RuntimeError(f"Encryption failed: {exc}") from exc

    def decrypt(self, encrypted_text: str, strict: bool = False) -> str:
        """Decrypt encrypted text

        Args:
            encrypted_text: Encrypted text to decrypt
            strict: If True, raise exception on error. If False (default), return empty string
        """
        if not encrypted_text:
            return ""  # Allow empty strings for optional fields
        try:
            return self.cipher.decrypt(str(encrypted_text).encode()).decode()
        except InvalidToken as exc:
            logger.error(f"Şifre çözme hatası (anahtar uyumsuz): {exc}")
            if strict:
                raise RuntimeError(f"Decryption failed - invalid token: {exc}") from exc
            else:
                logger.warning("Invalid token, returning empty string for backwards compatibility")
                return ""
        except Exception as exc:
            logger.error(f"Şifre çözme hatası: {exc}")
            if strict:
                raise RuntimeError(f"Decryption failed: {exc}") from exc
            else:
                logger.warning("Decryption failed, returning empty string for backwards compatibility")
                return ""


encryption_manager = EncryptionManager()