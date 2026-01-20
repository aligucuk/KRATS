# services/sms_service.py

from typing import Tuple
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class SMSService:
    """SMS notification service (Twilio)"""
    
    def __init__(self, db):
        """Initialize SMS service
        
        Args:
            db: Database manager instance
        """
        self.db = db
        self.enabled = settings.SMS_ENABLED
        
        if self.enabled and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                self.client = Client(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
                self.from_number = settings.TWILIO_PHONE_NUMBER
                logger.info("Twilio SMS service initialized")
            except Exception as e:
                logger.error(f"Twilio initialization failed: {e}")
                self.client = None
        else:
            self.client = None
            logger.info("SMS service disabled or not configured")
    
    def send_sms(self, to_number: str, message: str) -> Tuple[bool, str]:
        """Send SMS message
        
        Args:
            to_number: Recipient phone number
            message: Message content
            
        Returns:
            Tuple of (success, message_sid or error)
        """
        if not self.enabled:
            logger.debug("SMS service disabled")
            return False, "SMS servisi kapalı"
        
        if not self.client:
            logger.warning("SMS client not initialized")
            return False, "SMS servisi yapılandırılmamış"
        
        try:
            # Clean and format phone number
            clean_number = self._format_phone_number(to_number)
            
            if not clean_number:
                return False, "Geçersiz telefon numarası"
            
            # Send SMS via Twilio
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=clean_number
            )
            
            logger.info(f"SMS sent to {clean_number} - SID: {message_obj.sid}")
            
            # Log to database
            self.db.add_audit_log(
                user_id=1,  # System
                action_type="SMS_SENT",
                description=f"SMS sent to {clean_number}"
            )
            
            return True, message_obj.sid
        
        except TwilioRestException as e:
            logger.error(f"Twilio API error: {e}")
            return False, f"Twilio hatası: {e.msg}"
        except Exception as e:
            logger.error(f"SMS send failed: {e}")
            return False, f"SMS gönderilemedi: {str(e)}"
    
    def send_appointment_reminder(
        self, patient_name: str, phone: str,
        date_str: str, time_str: str
    ) -> Tuple[bool, str]:
        """Send appointment reminder SMS
        
        Args:
            patient_name: Patient name
            phone: Phone number
            date_str: Appointment date
            time_str: Appointment time
            
        Returns:
            Tuple of (success, message)
        """
        # Get SMS template from database
        template = self.db.get_setting("sms_template") or \
            "Sayın {hasta}, {tarih} {saat} tarihindeki randevunuzu hatırlatırız. - KRATS Klinik"
        
        # Format message
        message = template.format(
            hasta=patient_name,
            tarih=date_str,
            saat=time_str
        )
        
        return self.send_sms(phone, message)
    
    def _format_phone_number(self, phone: str) -> str:
        """Format phone number for international use
        
        Args:
            phone: Phone number string
            
        Returns:
            Formatted phone number with country code
        """
        # Remove non-digits
        clean = ''.join(filter(str.isdigit, phone))
        
        if not clean:
            return ""
        
        # Add Turkey country code if needed
        if len(clean) == 10 and clean.startswith('5'):
            clean = '90' + clean
        
        # Add + prefix
        if not clean.startswith('+'):
            clean = '+' + clean
        
        return clean
    
    def get_balance(self) -> Tuple[bool, str]:
        """Get Twilio account balance
        
        Returns:
            Tuple of (success, balance_info)
        """
        if not self.client:
            return False, "SMS servisi yapılandırılmamış"
        
        try:
            account = self.client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
            balance = self.client.balance.fetch()
            
            return True, f"Bakiye: {balance.balance} {balance.currency}"
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return False, str(e)


# Global instance will be created when needed