# services/enabiz_service.py

import uuid
import requests
from datetime import datetime
from typing import Dict, Tuple, Optional
from xml.sax.saxutils import escape

from config import settings
from utils.logger import get_logger
from utils.encryption_manager import encryption_manager
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
                tracking_id = str(uuid.uuid4())[:10].upper()
                
                logger.info(f"E-Nabız submission successful - Tracking: {tracking_id}")
                
                return {
                    'status': 'success',
                    'message': 'E-Nabız sunucusuna iletildi',
                    'details': 'İşlem Başarılı',
                    'tracking_id': tracking_id
                }
            else:
                logger.error(f"E-Nabız API error: {response.status_code}")
                return {
                    'status': 'error',
                    'message': f'API hatası: {response.status_code}',
                    'details': response.text[:200]
                }
        
        except requests.exceptions.Timeout:
            logger.error("E-Nabız request timeout")
            return {
                'status': 'error',
                'message': 'Zaman aşımı - Sunucuya ulaşılamadı'
            }
        except Exception as e:
            logger.error(f"E-Nabız integration failed: {e}")
            return {
                'status': 'error',
                'message': f'Entegrasyon hatası: {str(e)}'
            }
    
    def _generate_sys_xml(
        self, patient: Dict, appointment: Dict, doctor_tc: str
    ) -> str:
        """Generate SYS XML message
        
        Args:
            patient: Patient data
            appointment: Appointment data
            doctor_tc: Doctor TC number
            
        Returns:
            XML string
        """
        # Escape user inputs for XML safety
        p_tc = escape(str(patient.get('tc_no', '')))
        p_name = escape(str(patient.get('name', '')))
        d_tc = escape(str(doctor_tc))
        
        # Generate unique message ID
        message_guid = str(uuid.uuid4())
        
        # Current timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        
        # Get ICD code from appointment
        icd_code = appointment.get('icd_code', 'Z00.0')  # Default: General medical exam
        
        # Determine gender code (1=Male, 2=Female)
        gender_code = '1' if patient.get('gender') == 'Erkek' else '2'
        
        # Build XML
        xml = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <SYSSendMessage xmlns="http://saglik.gov.tr/">
      <input>
        <SYSMessage>
          <messageGuid>{message_guid}</messageGuid>
          <messageType>101</messageType>
          <documentGenerationTime>{timestamp}</documentGenerationTime>
          <author>
            <healthCareProvider>{self.firm_code}</healthCareProvider>
            <user>{self.username}</user>
            <password>{self.password}</password>
          </author>
          <recordData>
            <patient>
              <id>{p_tc}</id>
              <name>{p_name}</name>
              <gender>{gender_code}</gender>
            </patient>
            <transaction>
              <date>{appointment.get('date', timestamp)}</date>
              <doctor>
                <id>{d_tc}</id>
              </doctor>
              <diagnosis>
                <code>{icd_code}</code>
              </diagnosis>
            </transaction>
          </recordData>
        </SYSMessage>
      </input>
    </SYSSendMessage>
  </soap:Body>
</soap:Envelope>"""
        
        return xml.strip()
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test E-Nabız connection
        
        Returns:
            Tuple of (success, message)
        """
        if not self.enabled:
            return False, "E-Nabız kapalı"
        
        try:
            # Test with dummy data
            test_patient = {
                'tc_no': '12345678901',
                'name': 'Test Hasta',
                'gender': 'Erkek'
            }
            
            test_appointment = {
                'date': datetime.now().strftime("%Y%m%d%H%M"),
                'icd_code': 'Z00.0'
            }
            
            result = self.send_examination_data(
                test_patient, test_appointment, "11111111111"
            )
            
            if result['status'] == 'success':
                return True, "Bağlantı başarılı"
            else:
                return False, result['message']
        
        except Exception as e:
            return False, str(e)


# Global instance will be created by pages when needed