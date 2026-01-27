# database/models.py

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, 
    Boolean, ForeignKey, Table, Enum
)
from sqlalchemy.orm import relationship, declarative_base, synonym
from sqlalchemy.sql import func
import enum

Base = declarative_base()


# ==================== ENUMS ====================

class UserRole(enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doktor"
    SECRETARY = "sekreter"
    ACCOUNTANT = "muhasebe"


class AppointmentStatus(enum.Enum):
    WAITING = "Bekliyor"
    IN_PROGRESS = "Görüşülüyor"
    COMPLETED = "Tamamlandı"
    CANCELLED = "İptal"
    NO_SHOW = "Gelmedi"


class PatientStatus(enum.Enum):
    NEW = "Yeni"
    ACTIVE = "Aktif"
    ARCHIVED = "Arşiv"


class TransactionType(enum.Enum):
    INCOME = "Gelir"
    EXPENSE = "Gider"


# ==================== MODELS ====================

class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)  # bcrypt hash
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.SECRETARY)
    specialty = Column(String(50), default="Genel")
    commission_rate = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_login = Column(DateTime)
    
    # Relationships
    appointments = relationship("Appointment", back_populates="doctor", foreign_keys="Appointment.doctor_id")
    messages_sent = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    messages_received = relationship("Message", back_populates="receiver", foreign_keys="Message.receiver_id")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role={self.role.value})>"


class Patient(Base):
    """Patient model with encrypted sensitive data"""
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tc_no = Column(String(255), unique=True, nullable=False, index=True)  # Encrypted
    full_name = Column(String(255), nullable=False)  # Encrypted
    phone = Column(String(255))  # Encrypted
    email = Column(String(100))
    birth_date = Column(String(50))
    gender = Column(String(10))
    address = Column(Text)  # Encrypted
    status = Column(Enum(PatientStatus), default=PatientStatus.NEW)
    source = Column(String(50), default="Diğer")  # How they found us
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    appointments = relationship("Appointment", back_populates="patient")
    medical_records = relationship("MedicalRecord", back_populates="patient")
    files = relationship("PatientFile", back_populates="patient")
    
    def __repr__(self):
        return f"<Patient(id={self.id}, status={self.status.value})>"

    @property
    def first_name(self) -> str:
        from utils.encryption_manager import encryption_manager

        decrypted = encryption_manager.decrypt(self.full_name) if self.full_name else ""
        return decrypted.split(" ", 1)[0] if decrypted else ""

    @property
    def last_name(self) -> str:
        from utils.encryption_manager import encryption_manager

        decrypted = encryption_manager.decrypt(self.full_name) if self.full_name else ""
        parts = decrypted.split()
        if len(parts) <= 1:
            return ""
        return " ".join(parts[1:])


class Appointment(Base):
    """Appointment scheduling"""
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    active_user_id = Column(Integer, ForeignKey("users.id"))  # Who created it
    
    appointment_date = Column(DateTime, nullable=False, index=True)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.WAITING)
    notes = Column(Text)  # Encrypted
    reminder_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("User", back_populates="appointments", foreign_keys=[doctor_id])
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, date={self.appointment_date}, status={self.status.value})>"


class MedicalRecord(Base):
    """Medical examination records"""
    __tablename__ = "medical_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    anamnez = Column(Text)  # Patient complaint
    diagnosis = Column(Text)  # Medical diagnosis
    treatment = Column(Text)  # Treatment plan
    prescription = Column(Text)  # Medications
    
    record_date = Column(DateTime, server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="medical_records")
    
    def __repr__(self):
        return f"<MedicalRecord(id={self.id}, patient_id={self.patient_id})>"


class Transaction(Base):
    """Financial transactions"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(Enum(TransactionType), nullable=False)
    category = Column(String(50), default="Genel")
    amount = Column(Float, nullable=False)
    description = Column(Text)
    transaction_date = Column(DateTime, nullable=False, index=True)
    
    created_at = Column(DateTime, server_default=func.now())

    transaction_type = synonym("type")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.type.value}, amount={self.amount})>"


class Product(Base):
    """Inventory/stock management"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    unit = Column(String(20))  # Adet, Kutu, Lt, etc.
    quantity = Column(Integer, default=0)
    threshold = Column(Integer, default=10)  # Low stock alert
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    inventory_logs = relationship("InventoryLog", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', qty={self.quantity})>"


class InventoryLog(Base):
    """Inventory movement history"""
    __tablename__ = "inventory_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    
    quantity = Column(Integer, nullable=False)  # Positive for add, negative for use
    log_date = Column(DateTime, server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="inventory_logs")
    
    def __repr__(self):
        return f"<InventoryLog(product_id={self.product_id}, qty={self.quantity})>"


class Message(Base):
    """Internal messaging system"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="messages_received")
    
    def __repr__(self):
        return f"<Message(id={self.id}, from={self.sender_id}, to={self.receiver_id})>"


class PatientFile(Base):
    """Patient uploaded files (X-rays, lab results, etc.)"""
    __tablename__ = "patient_files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))  # pdf, jpg, dcm, etc.
    file_size = Column(Integer)  # bytes
    
    upload_date = Column(DateTime, server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="files")
    
    def __repr__(self):
        return f"<PatientFile(id={self.id}, name='{self.file_name}')>"


class Setting(Base):
    """Application settings key-value store"""
    __tablename__ = "settings"
    
    key = Column(String(100), primary_key=True)
    value = Column(Text)
    
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<Setting(key='{self.key}')>"


class AuditLog(Base):
    """Audit trail for security and compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    action_type = Column(String(50), nullable=False)  # LOGIN, CREATE, UPDATE, DELETE
    description = Column(Text)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(255))
    
    created_at = Column(DateTime, server_default=func.now(), index=True)

    action = synonym("action_type")
    details = synonym("description")
    timestamp = synonym("created_at")
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action_type}')>"


class NewsSource(Base):
    """RSS news sources"""
    __tablename__ = "news_sources"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<NewsSource(id={self.id}, name='{self.name}')>"


class MedicalNews(Base):
    """Medical news articles"""
    __tablename__ = "medical_news"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    link = Column(String(1000), unique=True)
    source = Column(String(100))
    image_url = Column(String(1000))
    
    is_read = Column(Boolean, default=False)
    is_saved = Column(Boolean, default=False)
    
    published_date = Column(DateTime, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<MedicalNews(id={self.id}, title='{self.title[:50]}')>"


class NewsKeyword(Base):
    """Keywords for filtering news"""
    __tablename__ = "news_keywords"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(100), nullable=False, unique=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<NewsKeyword(id={self.id}, keyword='{self.keyword}')>"
