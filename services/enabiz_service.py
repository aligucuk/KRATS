# services/enabiz_service.py

import uuid
import requests
from datetime import datetime
from typing import Dict, Tuple, Optional
from xml.sax.saxutils import escape

from config import settings
from utils.logger import get_logger
from utils.encryption import encryption_manager
from utils.exceptions import IntegrationException

logger = get_logger(__name__)


class ENabizService:
    """E-Nabız (Turkish Ministry of Health) integration service"""
    
    def __init__(self, db):
        """Initialize E-Nabız service
        
        Args:
            db: Database manager instance
        """
        self.db = db
        self.enabled = settings.ENABIZ_ENABLED
        self.api_url = settings.ENABIZ_API_URL
        self.soap_action = "http://saglik.gov.tr/SYSSendMessage"
        
        # Get credentials from database
        self.username = self.db.get_setting("uss_username") or settings.ENABIZ_USS_USERNAME
        
        # Decrypt password
        encrypted_password = self.db.get_setting("uss_password")
        if encrypted_password:
            try:
                self.password = encryption_manager.decrypt(encrypted_password)
            except:
                self.password = settings.ENABIZ_USS_PASSWORD
        else:
            self.password = settings.ENABIZ_USS_PASSWORD
        
        self.firm_code = self.db.get_setting("uss_firm_code") or settings.ENABIZ_FIRM_CODE
        
        logger.info(f"E-Nabız service initialized - Enabled: {self.enabled}")
    
    def send_examination_data(
        self, patient_data: Dict, appointment_data: Dict,
        doctor_tc: str = "11111111111"
    ) -> Dict[str, str]:
        """Send examination data to E-Nabız
        
        Args:
            patient_data: Patient information dict
            appointment_data: Appointment/examination data dict
            doctor_tc: Doctor's TC ID number
            
        Returns:
            Result dictionary with status, message, tracking_id
        """
        if not self.enabled:
            return {
                'status': 'disabled',
                'message': 'E-Nabız entegrasyonu kapalı'
            }
        
        if not self.username or not self.password:
            return {
                'status': 'error',
                'message': 'E-Nabız kullanıcı bilgileri eksik'
            }
        
        try:
            # Generate XML payload
            xml_payload = self._generate_sys_xml(
                patient_data, appointment_data, doctor_tc
            )
            
            # Prepare SOAP envelope
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': self.soap_action
            }
            
            # Send request
            logger.info("Sending examination data to E-Nabız")
            
            response = requests.post(
                self.api_url,
                data=xml_payload.encode('utf-8'),
                headers=headers,
                timeout=30
            )
            
            # Parse response
            if response.status_code == 200:
                # Generate tracking ID
                tracking_id = str(uuid.uuid4())[