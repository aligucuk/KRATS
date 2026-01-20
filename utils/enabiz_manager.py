import uuid
import datetime
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape # Güvenlik için şart
from utils.security_manager import SecurityManager

class ENabizManager:
    def __init__(self, db):
        self.db = db
        self.uss_username = self.db.get_setting("uss_username")
        
        # Şifre çözme işlemi
        encrypted_pass = self.db.get_setting("uss_password")
        self.uss_password = ""
        if encrypted_pass:
            try:
                sec = SecurityManager()
                self.uss_password = sec.decrypt(encrypted_pass)
            except: pass
        
        self.kurum_kodu = self.db.get_setting("uss_firm_code") or "0000"

    def send_examination_data(self, patient_data, appointment_data, doctor_tc="11111111111"):
        """
        Bakanlığa veri gönderimini simüle eder.
        """
        try:
            # 1. XML Hazırla
            xml_payload = self._generate_sys_xml(patient_data, appointment_data, doctor_tc)
            
            # --- XML GÖNDERİM SİMÜLASYONU ---
            # Gerçekte: response = requests.post(...)
            
            # Loglama için güvenli XML (Şifreyi gizle)
            safe_xml = xml_payload.replace(self.uss_password, "********") if self.uss_password else xml_payload
            
            # Rastgele bir takip no üret
            fake_tracking_id = str(uuid.uuid4())[:10].upper()
            
            # Başarılı cevap simülasyonu
            return {
                "status": "success",
                "message": "e-Nabız sunucusuna iletildi.",
                "details": "İşlem Başarılı",
                "tracking_id": fake_tracking_id,
                "debug_xml": safe_xml # Debug için maskelenmiş XML'i dönebiliriz
            }

        except Exception as e:
            return {
                "status": "error", 
                "message": f"Entegrasyon Hatası: {str(e)}"
            }

    def _generate_sys_xml(self, patient, appointment, doctor_tc):
        # GÜVENLİK: Kullanıcı girdilerini escape ediyoruz
        # Eğer isimde "<" veya "&" varsa XML bozulmaz.
        p_tc = escape(str(patient.get('tc_no', '')))
        p_name = escape(str(patient.get('name', '')))
        d_tc = escape(str(doctor_tc))
        
        now = datetime.datetime.now().strftime("%Y%m%d%H%M")
        guid = str(uuid.uuid4())
        
        # XML String (Formatlanmış)
        # Not: F-String kullanırken escape edilmiş değişkenleri kullanıyoruz.
        xml = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <SYSSendMessage xmlns="http://saglik.gov.tr/">
      <input>
        <SYSMessage>
          <messageGuid>{guid}</messageGuid>
          <messageType>101</messageType>
          <documentGenerationTime>{now}</documentGenerationTime>
          <author>
            <healthCareProvider>{self.kurum_kodu}</healthCareProvider>
            <user>{self.uss_username}</user>
            <password>{self.uss_password}</password>
          </author>
          <recordData>
            <patient>
              <id>{p_tc}</id>
              <name>{p_name}</name>
              <gender>{'1' if patient.get('gender') == 'E' else '2'}</gender>
            </patient>
            <transaction>
              <date>{appointment.get('date', now)}</date>
              <doctor><id>{d_tc}</id></doctor>
              <diagnosis>
                 <code>{appointment.get('icd_code', 'Z00.0')}</code>
              </diagnosis>
            </transaction>
          </recordData>
        </SYSMessage>
      </input>
    </SYSSendMessage>
  </soap:Body>
</soap:Envelope>"""
        return xml.strip()