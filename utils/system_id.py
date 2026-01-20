import hashlib
import logging
import platform
import uuid

logger = logging.getLogger("SystemIdManager")


class SystemIdManager:
    """Cihaz parmak izi üretimi için yardımcı sınıf."""

    def get_device_fingerprint(self) -> str:
        raw_value = "|".join(
            [
                platform.node(),
                platform.system(),
                platform.release(),
                platform.machine(),
                str(uuid.getnode()),
            ]
        )

        if not raw_value.strip("|"):
            logger.warning("Cihaz bilgisi alınamadı, varsayılan değer kullanılıyor.")
            raw_value = str(uuid.uuid4())

        return hashlib.sha256(raw_value.encode()).hexdigest()


system_id_manager = SystemIdManager()


def get_device_fingerprint() -> str:
    return system_id_manager.get_device_fingerprint()