cat > database/models_skrs.py << 'ENDOFFILE'
# database/models_skrs.py
"""
SKRS (Sağlık Kodlama Referans Sunucusu) Veritabanı Modelleri
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean
from sqlalchemy.sql import func
from database.models import Base

# ==================== SKRS MODELS ====================

class SKRSICDCode(Base):
    """ICD-10 Tanı Kodları"""
    __tablename__ = "skrs_icd_codes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name_tr = Column(String(500), nullable=False)
    name_en = Column(String(500))
    category = Column(String(100))
    version = Column(String(20), default="ICD-10")
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<SKRSICDCode(code='{self.code}', name='{self.name_tr[:30]}')>"


class SKRSMedication(Base):
    """İlaç Listesi (MEDULA)"""
    __tablename__ = "skrs_medications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    barcode = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=False, index=True)
    active_ingredient = Column(String(300))
    dosage_form = Column(String(100))
    strength = Column(String(50))
    package_size = Column(String(50))
    manufacturer = Column(String(200))
    atc_code = Column(String(10))
    price = Column(Float)
    is_prescription = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<SKRSMedication(barcode='{self.barcode}', name='{self.name[:30]}')>"


class SKRSProcedure(Base):
    """Tetkik/İşlem Kodları (SUT)"""
    __tablename__ = "skrs_procedures"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    category = Column(String(100))
    sub_category = Column(String(100))
    price = Column(Float)
    points = Column(Float)
    requires_approval = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<SKRSProcedure(code='{self.code}', name='{self.name[:30]}')>"


class SKRSSpecialty(Base):
    """Doktor Uzmanlık Kodları"""
    __tablename__ = "skrs_specialties"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_short = Column(String(50))
    branch_type = Column(String(50))
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<SKRSSpecialty(code='{self.code}', name='{self.name}')>"


class SKRSInstitution(Base):
    """Kurum/Hastane Kodları"""
    __tablename__ = "skrs_institutions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=False)
    type = Column(String(100))
    city = Column(String(50))
    district = Column(String(50))
    address = Column(Text)
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<SKRSInstitution(code='{self.code}', name='{self.name[:30]}')>"


class SKRSSyncLog(Base):
    """SKRS Senkronizasyon Logları"""
    __tablename__ = "skrs_sync_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(100), nullable=False)
    sync_type = Column(String(50))
    records_added = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_deleted = Column(Integer, default=0)
    sync_duration = Column(Float)
    sync_date = Column(DateTime, server_default=func.now())
    status = Column(String(20))
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<SKRSSyncLog(table='{self.table_name}', status='{self.status}')>"


# ==================== SEED DATA ====================

SAMPLE_ICD_CODES = [
    {"code": "J00", "name": "Akut nazofarenjit (soğuk algınlığı)", "category": "Solunum"},
    {"code": "J06.9", "name": "Akut üst solunum yolu enfeksiyonu", "category": "Solunum"},
    {"code": "J11", "name": "Grip, virüs tanımlanmamış", "category": "Solunum"},
    {"code": "K29.7", "name": "Gastrit", "category": "Sindirim"},
    {"code": "R05", "name": "Öksürük", "category": "Belirtiler"},
    {"code": "R50.9", "name": "Ateş", "category": "Belirtiler"},
    {"code": "R51", "name": "Baş ağrısı", "category": "Belirtiler"},
    {"code": "M79.1", "name": "Kas ağrısı", "category": "Kas-İskelet"},
    {"code": "Z00.0", "name": "Genel tıbbi muayene", "category": "Muayene"},
]

SAMPLE_MEDICATIONS = [
    {
        "barcode": "8699514360012",
        "name": "PAROL 500 MG 20 TABLET",
        "active_ingredient": "Parasetamol",
        "strength": "500mg",
        "form": "Tablet",
        "package": "20 tablet"
    },
]

SAMPLE_SPECIALTIES = [
    {"code": "000", "name": "Genel Pratisyen", "short": "Pratisyen"},
    {"code": "100", "name": "İç Hastalıkları", "short": "Dahiliye"},
    {"code": "300", "name": "Kadın Hastalıkları ve Doğum", "short": "Kadın Doğum"},
]


def seed_skrs_data(session):
    """Başlangıç SKRS verilerini yükle"""
    
    # ICD-10 kodları
    for item in SAMPLE_ICD_CODES:
        existing = session.query(SKRSICDCode).filter_by(code=item["code"]).first()
        if not existing:
            session.add(SKRSICDCode(
                code=item["code"],
                name_tr=item["name"],
                category=item["category"],
                is_active=True
            ))
    
    # İlaçlar
    for item in SAMPLE_MEDICATIONS:
        existing = session.query(SKRSMedication).filter_by(barcode=item["barcode"]).first()
        if not existing:
            session.add(SKRSMedication(
                barcode=item["barcode"],
                name=item["name"],
                active_ingredient=item["active_ingredient"],
                strength=item["strength"],
                dosage_form=item["form"],
                package_size=item["package"],
                is_active=True
            ))
    
    # Uzmanlıklar
    for item in SAMPLE_SPECIALTIES:
        existing = session.query(SKRSSpecialty).filter_by(code=item["code"]).first()
        if not existing:
            session.add(SKRSSpecialty(
                code=item["code"],
                name=item["name"],
                name_short=item["short"],
                is_active=True
            ))
    
    session.commit()
    print("✅ SKRS seed data loaded")
ENDOFFILE