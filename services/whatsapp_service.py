# services/whatsapp_service.py

import time
import urllib.parse
from typing import Tuple, List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppService:
    """WhatsApp Business automation service"""
    
    def __init__(self, db):
        """Initialize WhatsApp service
        
        Args:
            db: Database manager instance
        """
        self.db = db
        self.enabled = settings.WHATSAPP_ENABLED
        self.driver = None
        
        logger.info(f"WhatsApp service initialized - Enabled: {self.enabled}")
    
    def start_session(self) -> Tuple[bool, str]:
        """Start WhatsApp Web session
        
        Returns:
            Tuple of (success, message)
        """
        if not self.enabled:
            return False, "WhatsApp servisi kapalı"
        
        try:
            logger.info("Starting WhatsApp Web session")
            
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            # Create driver
            if settings.WHATSAPP_CHROME_DRIVER_PATH:
                service = Service(settings.WHATSAPP_CHROME_DRIVER_PATH)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
            
            # Navigate to WhatsApp Web
            self.driver.get("https://web.whatsapp.com")
            
            logger.info("Please scan QR code in browser")
            
            # Wait for QR code to be scanned (check for chat list)
            try:
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
                    )
                )
                logger.info("WhatsApp Web connected successfully")
                return True, "WhatsApp Web bağlandı"
            except:
                return False, "QR kod taraması zaman aşımına uğradı"
        
        except Exception as e:
            logger.error(f"WhatsApp session start failed: {e}")
            return False, f"Bağlantı hatası: {str(e)}"
    
    def send_message(
        self, phone: str, message: str
    ) -> Tuple[bool, str]:
        """Send WhatsApp message
        
        Args:
            phone: Phone number (with country code)
            message: Message content
            
        Returns:
            Tuple of (success, message)
        """
        if not self.driver:
            return False, "WhatsApp oturumu başlatılmamış"
        
        try:
            # Clean phone number
            clean_phone = ''.join(filter(str.isdigit, phone))
            
            # Add Turkey country code if needed
            if len(clean_phone) == 10 and clean_phone.startswith('5'):
                clean_phone = '90' + clean_phone
            
            # Encode message
            encoded_msg = urllib.parse.quote(message)
            
            # Navigate to WhatsApp URL
            url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"
            self.driver.get(url)
            
            # Wait for send button
            send_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//span[@data-icon="send"]')
                )
            )
            
            # Click send
            send_button.click()
            
            # Wait for message to be sent
            time.sleep(3)
            
            logger.info(f"WhatsApp message sent to {clean_phone}")
            return True, "Mesaj gönderildi"
        
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return False, f"Gönderim hatası: {str(e)}"
    
    def send_bulk_reminders(
        self, appointments: List[Dict]
    ) -> Tuple[int, int]:
        """Send bulk appointment reminders
        
        Args:
            appointments: List of appointment dictionaries
            
        Returns:
            Tuple of (success_count, failure_count)
        """
        if not self.driver:
            logger.error("WhatsApp session not started")
            return 0, len(appointments)
        
        success_count = 0
        failure_count = 0
        
        # Get message template
        template = self.db.get_setting("whatsapp_template") or \
            "Merhaba {hasta}, yarın saat {saat} randevunuzu hatırlatırız. Sağlıklı günler dileriz."
        
        for appt in appointments:
            try:
                patient_name = appt.get('patient_name', '')
                phone = appt.get('phone', '')
                appt_time = appt.get('time', '')
                
                # Format message
                message = template.format(
                    hasta=patient_name,
                    saat=appt_time
                )
                
                # Send message
                success, _ = self.send_message(phone, message)
                
                if success:
                    success_count += 1
                    # Mark as sent in database
                    if 'id' in appt:
                        self.db.mark_reminder_sent(appt['id'])
                else:
                    failure_count += 1
                
                # Short delay between messages
                time.sleep(5)
            
            except Exception as e:
                logger.error(f"Failed to send reminder: {e}")
                failure_count += 1
        
        logger.info(f"Bulk reminders sent: {success_count} success, {failure_count} failed")
        return success_count, failure_count
    
    def close_session(self):
        """Close WhatsApp session"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("WhatsApp session closed")
            except Exception as e:
                logger.error(f"Error closing session: {e}")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close_session()


# Global instance will be created when needed