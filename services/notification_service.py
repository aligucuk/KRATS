# services/notification_service.py

import time
import smtplib
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import settings
from utils.logger import get_logger
from database.db_manager import DatabaseManager

logger = get_logger(__name__)


class NotificationService:
    """Background notification service for appointment reminders"""
    
    def __init__(self, db: DatabaseManager):
        """Initialize notification service
        
        Args:
            db: Database manager instance
        """
        self.db = db
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.last_check = None
        
        # Service configuration
        self.check_interval = 3600  # 1 hour
        self.enabled = True
        
        logger.info("Notification service initialized")
    
    def start(self):
        """Start notification service in background thread"""
        if self.is_running:
            logger.warning("Notification service already running")
            return
        
        self.is_running = True
        self.thread = threading.Thread(
            target=self._run_loop,
            name="NotificationService",
            daemon=True
        )
        self.thread.start()
        logger.info("Notification service started")
    
    def stop(self):
        """Stop notification service"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Notification service stopped")
    
    def _run_loop(self):
        """Main service loop"""
        logger.info("Notification service loop started")
        
        while self.is_running:
            try:
                # Check and send reminders
                self.check_and_send_reminders()
                
                # Daily maintenance tasks
                self.run_daily_maintenance()
                
                # Sleep until next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Notification service error: {e}")
                time.sleep(60)  # Short sleep on error
    
    def check_and_send_reminders(self):
        """Check for pending reminders and send them"""
        if not self.enabled:
            return
        
        try:
            # Get pending reminders
            pending = self.db.get_pending_reminders()
            
            if not pending:
                logger.debug("No pending reminders")
                return
            
            logger.info(f"Processing {len(pending)} pending reminders")
            
            # Get templates
            sms_template = self.db.get_setting("sms_template") or \
                "Sayın {hasta}, yarın {tarih} {saat} randevunuzu hatırlatırız."
            email_template = self.db.get_setting("email_template") or \
                "Sayın {hasta},\n\nYarın {tarih} saat {saat} randevunuzu hatırlatırız.\n\nSağlıklı günler."
            
            sent_count = 0
            
            for reminder in pending:
                try:
                    # Parse appointment data
                    appt_id = reminder['id']
                    patient_name = reminder['patient_name']
                    phone = reminder['phone']
                    email = reminder['email']
                    appt_date = reminder['appointment_date']
                    
                    # Format date/time
                    if isinstance(appt_date, str):
                        appt_date = datetime.strptime(appt_date, "%Y-%m-%d %H:%M")
                    
                    date_str = appt_date.strftime("%d.%m.%Y")
                    time_str = appt_date.strftime("%H:%M")
                    
                    # Prepare messages
                    sms_message = sms_template.format(
                        hasta=patient_name,
                        tarih=date_str,
                        saat=time_str
                    )
                    
                    email_body = email_template.format(
                        hasta=patient_name,
                        tarih=date_str,
                        saat=time_str
                    )
                    
                    # Send notifications
                    sent_any = False
                    
                    # Send SMS
                    if settings.SMS_ENABLED and phone:
                        if self.send_sms(phone, sms_message):
                            sent_any = True
                            logger.info(f"SMS sent to {phone}")
                    
                    # Send Email
                    if settings.EMAIL_ENABLED and email and '@' in email:
                        if self.send_email(
                            email,
                            "Randevu Hatırlatması",
                            email_body
                        ):
                            sent_any = True
                            logger.info(f"Email sent to {email}")
                    
                    # Mark as sent
                    if sent_any:
                        self.db.mark_reminder_sent(appt_id)
                        sent_count += 1
                
                except Exception as e:
                    logger.error(f"Failed to send reminder: {e}")
            
            logger.info(f"Sent {sent_count} reminders")
            
        except Exception as e:
            logger.error(f"Reminder check failed: {e}")
    
    def send_sms(self, phone: str, message: str) -> bool:
        """Send SMS notification
        
        Args:
            phone: Phone number
            message: Message content
            
        Returns:
            True if sent successfully
        """
        try:
            # Clean phone number
            phone = ''.join(filter(str.isdigit, phone))
            
            if not phone:
                return False
            
            # Add country code if needed
            if len(phone) == 10 and phone.startswith('5'):
                phone = '90' + phone
            
            # For development/testing, just log
            logger.info(f"[SMS] To: {phone}, Message: {message}")
            
            # Production: Integrate with SMS provider (Twilio, etc.)
            # from twilio.rest import Client
            # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            # client.messages.create(to=phone, from_=settings.TWILIO_PHONE_NUMBER, body=message)
            
            return True
            
        except Exception as e:
            logger.error(f"SMS send failed: {e}")
            return False
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email notification
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body
            
        Returns:
            True if sent successfully
        """
        try:
            if not settings.EMAIL_ENABLED:
                return False
            
            # Detect SMTP server based on sender email
            sender_email = settings.SMTP_USERNAME
            sender_password = settings.SMTP_PASSWORD
            
            if not sender_email or not sender_password:
                logger.warning("SMTP credentials not configured")
                return False
            
            # Auto-detect SMTP server
            smtp_host = settings.SMTP_HOST
            smtp_port = settings.SMTP_PORT
            
            domain = sender_email.split('@')[-1].lower()
            if 'gmail.com' in domain:
                smtp_host = 'smtp.gmail.com'
                smtp_port = 587
            elif 'outlook.com' in domain or 'hotmail.com' in domain:
                smtp_host = 'smtp.office365.com'
                smtp_port = 587
            elif 'yahoo.com' in domain:
                smtp_host = 'smtp.mail.yahoo.com'
                smtp_port = 587
            elif 'yandex.com' in domain:
                smtp_host = 'smtp.yandex.com'
                smtp_port = 465
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Send email
            if smtp_port == 465:
                # SSL
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
            else:
                # TLS
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
                server.starttls()
            
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
            server.quit()
            
            logger.info(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False
    
    def run_daily_maintenance(self):
        """Run daily maintenance tasks"""
        now = datetime.now()
        
        # Run once per day
        if self.last_check and self.last_check.date() == now.date():
            return
        
        # Only run during business hours
        if now.hour < 9 or now.hour > 18:
            return
        
        try:
            logger.info("Running daily maintenance")
            
            # Cleanup old data
            self.db.cleanup_old_data()
            
            # Update last check
            self.last_check = now
            
            logger.info("Daily maintenance completed")
            
        except Exception as e:
            logger.error(f"Daily maintenance failed: {e}")
    
    def send_test_notification(
        self, phone: Optional[str] = None,
        email: Optional[str] = None
    ) -> dict:
        """Send test notification
        
        Args:
            phone: Phone number (optional)
            email: Email address (optional)
            
        Returns:
            Result dictionary
        """
        results = {}
        
        if phone:
            sms_sent = self.send_sms(phone, "Test mesajı - KRATS Klinik OS")
            results['sms'] = 'Başarılı' if sms_sent else 'Başarısız'
        
        if email:
            email_sent = self.send_email(
                email,
                "Test Email - KRATS",
                "Bu bir test mesajıdır."
            )
            results['email'] = 'Başarılı' if email_sent else 'Başarısız'
        
        return results