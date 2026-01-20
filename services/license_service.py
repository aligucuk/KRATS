# services/license_service.py

import json
import base64
from datetime import datetime
from typing import Tuple, Optional
from cryptography.fernet import Fernet, InvalidToken

from config import settings
from utils.logger import get_logger
from utils.system_id import system_id_manager
from utils.exceptions import LicenseException

logger = get_logger(__name__)


class LicenseService:
    """License validation and management service"""
    
    def __init__(self):
        """Initialize license service with encryption key from settings"""
        if not settings.LICENSE_SECRET_KEY:
            raise LicenseException("LICENSE_SECRET_KEY b'L33izrilqC9FgXtnRaae54vB62Clt6kDckDzBODoNXQ=' ")
        
        try:
            # Ensure key is bytes
            key = settings.LICENSE_SECRET_KEY
            if isinstance(key, str):
                key = key.encode()
            
            self.cipher = Fernet(key)
            logger.info("License service initialized")
            
        except Exception as e:
            logger.error(f"License service initialization failed: {e}")
            raise LicenseException(f"License initialization failed: {str(e)}")
    
    def validate_license(self, license_key: str) -> Tuple[bool, str, int, Optional[str]]:
        """Validate license key
        
        Args:
            license_key: Base64 encoded encrypted license
            
        Returns:
            Tuple of (is_valid, message, user_limit, expiry_date)
        """
        if not license_key:
            return False, "Lisans anahtarı girilmemiş", 0, None
        
        try:
            # Decode and decrypt
            decoded_bytes = base64.urlsafe_b64decode(license_key.encode())
            decrypted_data = self.cipher.decrypt(decoded_bytes)
            license_data = json.loads(decrypted_data.decode())
            
            # Validate structure
            required_fields = ['expiry', 'limit']
            if not all(field in license_data for field in required_fields):
                return False, "Geçersiz lisans formatı", 0, None
            
            # Check expiry date
            expiry_str = license_data.get('expiry')
            if expiry_str:
                try:
                    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
                    if datetime.now() > expiry_date:
                        return False, "Lisans süresi dolmuş", 0, expiry_str
                except ValueError:
                    return False, "Geçersiz tarih formatı", 0, None
            else:
                expiry_str = "Sınırsız"
            
            # Check hardware binding
            hw_id = license_data.get('hw_id')
            if hw_id:
                current_hw_id = system_id_manager.get_device_fingerprint()
                if hw_id != current_hw_id:
                    logger.warning(f"Hardware mismatch: Expected {hw_id}, got {current_hw_id}")
                    return False, "Bu lisans başka bir bilgisayara ait", 0, None
            
            # Get user limit
            user_limit = int(license_data.get('limit', 1))
            
            # Additional metadata
            company = license_data.get('company', '')
            logger.info(f"License validated successfully for {company}")
            
            return True, "Lisans geçerli", user_limit, expiry_str
            
        except InvalidToken:
            logger.warning("Invalid license token")
            return False, "Geçersiz lisans anahtarı", 0, None
        except json.JSONDecodeError:
            logger.warning("License JSON decode error")
            return False, "Bozuk lisans verisi", 0, None
        except Exception as e:
            logger.error(f"License validation error: {e}")
            return False, f"Doğrulama hatası: {str(e)}", 0, None
    
    def generate_license(
        self, company: str, user_limit: int,
        expiry_date: Optional[str] = None,
        bind_to_hardware: bool = False
    ) -> str:
        """Generate new license key (for license server use)
        
        Args:
            company: Company name
            user_limit: Maximum number of users
            expiry_date: Expiry date in YYYY-MM-DD format (None for unlimited)
            bind_to_hardware: Whether to bind to current hardware
            
        Returns:
            Base64 encoded license key
        """
        try:
            license_data = {
                'company': company,
                'limit': user_limit,
                'expiry': expiry_date,
                'issued': datetime.now().strftime("%Y-%m-%d"),
                'version': settings.APP_VERSION
            }
            
            # Add hardware binding
            if bind_to_hardware:
                license_data['hw_id'] = system_id_manager.get_device_fingerprint()
            
            # Encrypt and encode
            json_data = json.dumps(license_data)
            encrypted = self.cipher.encrypt(json_data.encode())
            license_key = base64.urlsafe_b64encode(encrypted).decode()
            
            logger.info(f"License generated for {company}")
            return license_key
            
        except Exception as e:
            logger.error(f"License generation failed: {e}")
            raise LicenseException(f"License generation failed: {str(e)}")
    
    def get_license_info(self, license_key: str) -> Optional[dict]:
        """Get license information without full validation
        
        Args:
            license_key: License key to decode
            
        Returns:
            License data dictionary or None
        """
        try:
            decoded_bytes = base64.urlsafe_b64decode(license_key.encode())
            decrypted_data = self.cipher.decrypt(decoded_bytes)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to get license info: {e}")
            return None
    
    def check_user_limit(self, license_key: str, current_users: int) -> Tuple[bool, str]:
        """Check if current user count is within license limit
        
        Args:
            license_key: License key
            current_users: Current number of active users
            
        Returns:
            Tuple of (within_limit, message)
        """
        is_valid, msg, limit, expiry = self.validate_license(license_key)
        
        if not is_valid:
            return False, msg
        
        if limit > 0 and current_users >= limit:
            return False, f"Kullanıcı kotası dolu ({current_users}/{limit})"
        
        return True, f"Kullanılabilir: {current_users}/{limit}"


# Global instance
license_service = LicenseService()