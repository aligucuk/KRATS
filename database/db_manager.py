# database/db_manager.py

from contextlib import contextmanager
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func, and_, or_, text
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from config import settings
from utils.logger import get_logger
from utils.exceptions import DatabaseException
from utils.security_manager import SecurityManager

# BU SATIRI EKLEYİN: Global security_manager nesnesi oluşturuluyor
security_manager = SecurityManager()
from utils.encryption_manager import encryption_manager
from .models import (
    Base, User, Patient, Appointment, Transaction, Product,
    Message, MedicalRecord, PatientFile, Setting, AuditLog,
    NewsSource, MedicalNews, NewsKeyword, InventoryLog,
    UserRole, AppointmentStatus, PatientStatus, TransactionType
)

logger = get_logger(__name__)


class DatabaseManager:
    """Production-ready database manager with connection pooling and security"""
    
    def __init__(self):
        """Initialize database connection and create tables"""
        try:
            # Create engine with connection pooling
            connect_args = {}
            
            if settings.DATABASE_URL.startswith("sqlite"):
                # SQLite specific settings
                connect_args = {
                    "check_same_thread": False,
                    "timeout": 30
                }
                
                # For in-memory databases
                if ":memory:" in settings.DATABASE_URL:
                    self.engine = create_engine(
                        settings.DATABASE_URL,
                        connect_args=connect_args,
                        poolclass=StaticPool,
                        echo=settings.DB_ECHO
                    )
                else:
                    self.engine = create_engine(
                        settings.DATABASE_URL,
                        connect_args=connect_args,
                        echo=settings.DB_ECHO
                    )
            else:
                # PostgreSQL/MySQL settings
                self.engine = create_engine(
                    settings.DATABASE_URL,
                    pool_size=settings.DB_POOL_SIZE,
                    max_overflow=settings.DB_MAX_OVERFLOW,
                    pool_pre_ping=True,  # Verify connections before use
                    echo=settings.DB_ECHO
                )
            
            # Create session factory
            session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(session_factory)
            
            # Create tables
            Base.metadata.create_all(self.engine)
            
            # Initialize default data
            self._initialize_defaults()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.critical(f"Database initialization failed: {e}")
            raise DatabaseException(f"Database initialization failed: {str(e)}")
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session with automatic cleanup
        
        Yields:
            SQLAlchemy session
            
        Example:
            with db.get_session() as session:
                user = session.query(User).filter_by(id=1).first()
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise DatabaseException(f"Database operation failed: {str(e)}")
        finally:
            session.close()
    
    def _initialize_defaults(self):
        """Initialize default data (admin user, settings, etc.)"""
        try:
            with self.get_session() as session:
                # Create default admin user
                admin = session.query(User).filter_by(username="admin").first()
                if not admin:
                    admin_password = security_manager.hash_password("admin")
                    admin = User(
                        username="admin",
                        password=admin_password,
                        full_name="Sistem Yöneticisi",
                        role=UserRole.ADMIN,
                        specialty="Genel"
                    )
                    session.add(admin)
                    logger.info("Default admin user created")
                
                # Create default settings
                default_settings = {
                    "country": "TR",
                    "theme_color": "teal",
                    "module_enabiz": "0",
                    "module_sms": "1",
                    "module_chat": "1",
                    "module_ai": "1",
                    "news_refresh_interval": "30",
                    "news_retention_days": "7",
                    "news_notifications": "1"
                }
                
                for key, value in default_settings.items():
                    existing = session.query(Setting).filter_by(key=key).first()
                    if not existing:
                        session.add(Setting(key=key, value=value))
                
                # Create default news sources
                default_sources = [
                    ("Google News - Tıp (TR)", "https://news.google.com/rss/search?q=sağlık+tıp+hastane&hl=tr&gl=TR&ceid=TR:tr"),
                    ("ScienceDaily", "https://www.sciencedaily.com/rss/health_medicine.xml"),
                    ("BBC Health", "http://feeds.bbci.co.uk/news/health/rss.xml")
                ]
                
                for name, url in default_sources:
                    existing = session.query(NewsSource).filter_by(url=url).first()
                    if not existing:
                        session.add(NewsSource(name=name, url=url))
                
                session.commit()
                logger.info("Default data initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize defaults: {e}")
    
    # ==================== USER MANAGEMENT ====================
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        try:
            # Session context'i içinde işlem yapıyoruz
            with self.get_session() as session:
                user = session.query(User).filter_by(
                    username=username,
                    is_active=True
                ).first()
                
                # Şifre kontrolü (Global security_manager kullanıyoruz)
                if user and security_manager.verify_password(password, user.password):
                    # Son girişi güncelle
                    user.last_login = datetime.now()
                    
                    # Değişikliği kaydet (Bu işlem nesneyi 'expire' eder)
                    session.commit()
                    
                    # KRİTİK DÜZELTME BURADA:
                    # 1. Verileri tazele (Refresh)
                    session.refresh(user)
                    # 2. Nesneyi session'dan ayır (Expunge). 
                    # Artık veritabanı bağlantısı kapansa bile bu nesne okunabilir.
                    session.expunge(user)
                    
                    self.add_audit_log(user.id, "LOGIN", f"User {username} logged in")
                    logger.info(f"User authenticated: {username}")
                    
                    return user
                else:
                    logger.warning(f"Authentication failed for user: {username}")
                    return None
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
        
    def create_user(
        self, username: str, password: str, full_name: str,
        role: str, commission_rate: int = 0, specialty: str = "Genel"
    ) -> bool:
        """Create new user with license validation
        
        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            full_name: Full name
            role: User role (admin, doktor, sekreter, muhasebe)
            commission_rate: Commission percentage
            specialty: Medical specialty
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate password strength
            is_valid, error_msg = security_manager.validate_password_strength(password)
            if not is_valid:
                return False
            
            with self.get_session() as session:
                # Check if username exists
                existing = session.query(User).filter_by(username=username).first()
                if existing:
                    return False
                
                # Check license limit (from settings or license)
                # This would integrate with license system
                user_count = session.query(User).filter_by(is_active=True).count()
                # TODO: Check against license limit
                
                # Hash password
                hashed_password = security_manager.hash_password(password)
                
                # Convert role string to enum
                if isinstance(role, UserRole):
                    role_enum = role
                else:
                    try:
                        role_enum = UserRole[str(role).upper()]
                    except KeyError:
                        role_enum = UserRole.SECRETARY
                
                # Create user
                user = User(
                    username=username,
                    password=hashed_password,
                    full_name=full_name,
                    role=role_enum,
                    commission_rate=commission_rate,
                    specialty=specialty
                )
                
                session.add(user)
                session.commit()
                
                logger.info(f"User created: {username}")
                return True
                
        except IntegrityError:
            return False
        except Exception as e:
            logger.error(f"User creation failed: {e}")
            return False
    
    def get_all_users(self) -> List[User]:
        """Get all active users"""
        try:
            with self.get_session() as session:
                return session.query(User).filter_by(is_active=True).all()
        except Exception as e:
            logger.error(f"Failed to fetch users: {e}")
            return []
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            with self.get_session() as session:
                return session.query(User).filter_by(id=user_id).first()
        except Exception as e:
            logger.error(f"Failed to fetch user: {e}")
            return None
    
    def update_user_password(self, user_id: int, new_password: str) -> Tuple[bool, str]:
        """Update user password
        
        Args:
            user_id: User ID
            new_password: New plain text password
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate password
            is_valid, error_msg = security_manager.validate_password_strength(new_password)
            if not is_valid:
                return False, error_msg
            
            with self.get_session() as session:
                user = session.query(User).filter_by(id=user_id).first()
                if not user:
                    return False, "Kullanıcı bulunamadı"
                
                # Hash new password
                user.password = security_manager.hash_password(new_password)
                session.commit()
                
                logger.info(f"Password updated for user: {user.username}")
                return True, "Şifre güncellendi"
                
        except Exception as e:
            logger.error(f"Password update failed: {e}")
            return False, "Şifre güncellenemedi"
    
    # ==================== PATIENT MANAGEMENT ====================
    
    def create_patient(
        self, tc_no: str, full_name: str, phone: str,
        birth_date: str, gender: str, address: str,
        email: Optional[str] = None, source: str = "Diğer"
    ) -> Tuple[bool, str, Optional[int]]:
        """Create new patient with encrypted data
        
        Args:
            tc_no: Turkish ID number
            full_name: Patient full name
            phone: Phone number
            birth_date: Birth date
            gender: Gender (Erkek/Kadın)
            address: Address
            email: Email (optional)
            source: How they found us
            
        Returns:
            Tuple of (success, message, patient_id)
        """
        try:
            with self.get_session() as session:
                # Encrypt sensitive data
                encrypted_tc = encryption_manager.encrypt(tc_no)
                encrypted_name = encryption_manager.encrypt(full_name)
                encrypted_phone = encryption_manager.encrypt(phone)
                encrypted_address = encryption_manager.encrypt(address)
                
                # Create patient
                patient = Patient(
                    tc_no=encrypted_tc,
                    full_name=encrypted_name,
                    phone=encrypted_phone,
                    email=email,
                    birth_date=birth_date,
                    gender=gender,
                    address=encrypted_address,
                    source=source,
                    status=PatientStatus.NEW
                )
                
                session.add(patient)
                session.commit()
                
                logger.info(f"Patient created: ID {patient.id}")
                return True, "Hasta kaydedildi", patient.id
                
        except IntegrityError:
            return False, "Bu TC kimlik numarası zaten kayıtlı", None
        except Exception as e:
            logger.error(f"Patient creation failed: {e}")
            return False, f"Hasta kaydedilemedi: {str(e)}", None

    def add_patient(
        self, tc_no: str, first_name: str, last_name: str, phone: str,
        email: Optional[str] = None, birth_date: str = None,
        address: str = "", gender: str = ""
    ) -> Optional[int]:
        """Compatibility wrapper for adding patients using separate name fields."""
        full_name = f"{first_name} {last_name}".strip()
        success, _, patient_id = self.create_patient(
            tc_no=tc_no,
            full_name=full_name,
            phone=phone,
            birth_date=birth_date,
            gender=gender,
            address=address,
            email=email,
        )
        return patient_id if success else None

    def get_patient(self, patient_id: int) -> Optional[Patient]:
        """Get patient model by ID."""
        try:
            with self.get_session() as session:
                patient = session.query(Patient).filter_by(id=patient_id).first()
                if patient:
                    session.expunge(patient)
                return patient
        except Exception as e:
            logger.error(f"Failed to fetch patient: {e}")
            return None

    def update_patient(self, patient_id: int, **updates) -> bool:
        """Update patient details."""
        try:
            with self.get_session() as session:
                patient = session.query(Patient).filter_by(id=patient_id).first()
                if not patient:
                    return False

                if "phone" in updates:
                    patient.phone = encryption_manager.encrypt(updates["phone"])
                if "email" in updates:
                    patient.email = updates["email"]
                if "address" in updates:
                    patient.address = encryption_manager.encrypt(updates["address"])
                if "first_name" in updates or "last_name" in updates:
                    first_name = updates.get("first_name", "")
                    last_name = updates.get("last_name", "")
                    full_name = " ".join(part for part in [first_name, last_name] if part)
                    if full_name:
                        patient.full_name = encryption_manager.encrypt(full_name)

                session.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update patient: {e}")
            return False
    
    def get_active_patients(self) -> List[Dict[str, Any]]:
        """Get all active (non-archived) patients with decrypted data"""
        try:
            with self.get_session() as session:
                patients = session.query(Patient).filter(
                    Patient.status != PatientStatus.ARCHIVED
                ).order_by(Patient.id.desc()).all()
                
                # Decrypt data
                result = []
                for p in patients:
                    result.append({
                        'id': p.id,
                        'tc_no': encryption_manager.decrypt(p.tc_no),
                        'full_name': encryption_manager.decrypt(p.full_name),
                        'phone': encryption_manager.decrypt(p.phone),
                        'email': p.email,
                        'birth_date': p.birth_date,
                        'gender': p.gender,
                        'address': encryption_manager.decrypt(p.address),
                        'status': p.status.value,
                        'source': p.source,
                        'created_at': p.created_at
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch patients: {e}")
            return []
    
    def get_archived_patients(self) -> List[Dict[str, Any]]:
        """Get archived patients"""
        try:
            with self.get_session() as session:
                patients = session.query(Patient).filter_by(
                    status=PatientStatus.ARCHIVED
                ).order_by(Patient.id.desc()).all()
                
                result = []
                for p in patients:
                    result.append({
                        'id': p.id,
                        'tc_no': encryption_manager.decrypt(p.tc_no),
                        'full_name': encryption_manager.decrypt(p.full_name),
                        'phone': encryption_manager.decrypt(p.phone),
                        'email': p.email,
                        'birth_date': p.birth_date,
                        'gender': p.gender,
                        'address': encryption_manager.decrypt(p.address),
                        'status': p.status.value,
                        'source': p.source
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch archived patients: {e}")
            return []
    
    def get_patient_by_id(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """Get patient by ID with decrypted data"""
        try:
            with self.get_session() as session:
                patient = session.query(Patient).filter_by(id=patient_id).first()
                
                if not patient:
                    return None
                
                return {
                    'id': patient.id,
                    'tc_no': encryption_manager.decrypt(patient.tc_no),
                    'full_name': encryption_manager.decrypt(patient.full_name),
                    'phone': encryption_manager.decrypt(patient.phone),
                    'email': patient.email,
                    'birth_date': patient.birth_date,
                    'gender': patient.gender,
                    'address': encryption_manager.decrypt(patient.address),
                    'status': patient.status.value,
                    'source': patient.source,
                    'created_at': patient.created_at
                }
                
        except Exception as e:
            logger.error(f"Failed to fetch patient: {e}")
            return None
    
    def archive_patient(self, patient_id: int) -> bool:
        """Archive patient"""
        try:
            with self.get_session() as session:
                patient = session.query(Patient).filter_by(id=patient_id).first()
                if patient:
                    patient.status = PatientStatus.ARCHIVED
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to archive patient: {e}")
            return False
    
    def restore_patient(self, patient_id: int) -> bool:
        """Restore archived patient"""
        try:
            with self.get_session() as session:
                patient = session.query(Patient).filter_by(id=patient_id).first()
                if patient:
                    patient.status = PatientStatus.ACTIVE
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to restore patient: {e}")
            return False
    
    def search_patients(self, query: str) -> List[Patient]:
        """Search patients by name, TC, or phone."""
        try:
            with self.get_session() as session:
                patients = session.query(Patient).filter(
                    Patient.status != PatientStatus.ARCHIVED
                ).all()

                query_lower = query.lower()
                results = []
                for patient in patients:
                    full_name = encryption_manager.decrypt(patient.full_name).lower()
                    tc_no = encryption_manager.decrypt(patient.tc_no)
                    phone = encryption_manager.decrypt(patient.phone)
                    if (
                        query_lower in full_name
                        or query_lower in tc_no
                        or query_lower in phone
                    ):
                        session.expunge(patient)
                        results.append(patient)

                return results
        except Exception as e:
            logger.error(f"Patient search failed: {e}")
            return []

    def get_all_patients(self) -> List[Patient]:
        """Get all patients."""
        try:
            with self.get_session() as session:
                patients = session.query(Patient).all()
                for patient in patients:
                    session.expunge(patient)
                return patients
        except Exception as e:
            logger.error(f"Failed to fetch patients: {e}")
            return []
    
    def get_patient_count(self) -> int:
        """Get total patient count"""
        try:
            with self.get_session() as session:
                return session.query(Patient).filter(
                    Patient.status != PatientStatus.ARCHIVED
                ).count()
        except Exception as e:
            logger.error(f"Failed to count patients: {e}")
            return 0
    
    def get_patient_sources(self) -> List[Tuple[str, int]]:
        """Get patient distribution by source"""
        try:
            with self.get_session() as session:
                results = session.query(
                    Patient.source,
                    func.count(Patient.id)
                ).filter(
                    Patient.status != PatientStatus.ARCHIVED
                ).group_by(Patient.source).all()
                
                return [(source, count) for source, count in results]
                
        except Exception as e:
            logger.error(f"Failed to get patient sources: {e}")
            return []
    
    # ==================== APPOINTMENT MANAGEMENT ====================
    
    def create_appointment(
        self, patient_id: int, doctor_id: int,
        appointment_date: datetime, notes: str = "",
        active_user_id: Optional[int] = None
    ) -> Optional[int]:
        """Create new appointment
        
        Args:
            patient_id: Patient ID
            doctor_id: Doctor ID
            appointment_date: Appointment datetime
            notes: Optional notes
            active_user_id: ID of user creating the appointment
            
        Returns:
            Appointment ID if created, otherwise None.
        """
        try:
            with self.get_session() as session:
                appointment = Appointment(
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    appointment_date=appointment_date,
                    notes=notes or "",
                    active_user_id=active_user_id,
                    status=AppointmentStatus.WAITING
                )
                
                session.add(appointment)
                session.commit()
                
                logger.info(f"Appointment created: ID {appointment.id}")
                return appointment.id
                
        except Exception as e:
            logger.error(f"Appointment creation failed: {e}")
            return None

    @staticmethod
    def _maybe_decrypt(value: str) -> str:
        if not value:
            return ""
        if isinstance(value, str) and value.startswith("gAAAA"):
            return encryption_manager.decrypt(value)
        return value
    
    def get_todays_appointments(self) -> List[Dict[str, Any]]:
        """Get today's appointments"""
        try:
            with self.get_session() as session:
                today = datetime.now().date()
                tomorrow = today + timedelta(days=1)
                
                appointments = session.query(
                    Appointment, Patient
                ).join(Patient).filter(
                    and_(
                        Appointment.appointment_date >= today,
                        Appointment.appointment_date < tomorrow
                    )
                ).order_by(Appointment.appointment_date).all()
                
                result = []
                for appt, patient in appointments:
                    result.append({
                        'id': appt.id,
                        'patient_name': encryption_manager.decrypt(patient.full_name),
                        'patient_id': patient.id,
                        'appointment_date': appt.appointment_date,
                        'status': appt.status.value,
                        'notes': self._maybe_decrypt(appt.notes)
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch today's appointments: {e}")
            return []
    
    def get_appointments_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get appointments within date range"""
        try:
            with self.get_session() as session:
                appointments = session.query(
                    Appointment, Patient, User
                ).join(Patient).join(User, Appointment.doctor_id == User.id).filter(
                    and_(
                        Appointment.appointment_date >= start_date,
                        Appointment.appointment_date <= end_date
                    )
                ).order_by(Appointment.appointment_date).all()
                
                result = []
                for appt, patient, doctor in appointments:
                    result.append({
                        'id': appt.id,
                        'patient_name': encryption_manager.decrypt(patient.full_name),
                        'patient_tc': encryption_manager.decrypt(patient.tc_no),
                        'doctor_name': doctor.full_name,
                        'appointment_date': appt.appointment_date,
                        'status': appt.status.value,
                        'notes': self._maybe_decrypt(appt.notes)
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch appointments: {e}")
            return []

    def get_appointments_for_date(self, date: datetime.date) -> List[Appointment]:
        """Get appointments for a specific date."""
        try:
            with self.get_session() as session:
                start = datetime.combine(date, datetime.min.time())
                end = datetime.combine(date, datetime.max.time())
                appointments = session.query(Appointment).filter(
                    and_(
                        Appointment.appointment_date >= start,
                        Appointment.appointment_date <= end
                    )
                ).all()
                for appointment in appointments:
                    session.expunge(appointment)
                return appointments
        except Exception as e:
            logger.error(f"Failed to fetch appointments for date: {e}")
            return []
    
    def update_appointment_status(
        self, appointment_id: int, status: str
    ) -> bool:
        """Update appointment status"""
        try:
            with self.get_session() as session:
                appointment = session.query(Appointment).filter_by(id=appointment_id).first()
                if appointment:
                    if isinstance(status, AppointmentStatus):
                        status_enum = status
                    else:
                        try:
                            status_enum = AppointmentStatus[str(status).upper().replace("İ", "I")]
                        except KeyError:
                            # Try by value
                            for s in AppointmentStatus:
                                if s.value == status:
                                    status_enum = s
                                    break
                            else:
                                return False
                    
                    appointment.status = status_enum
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to update appointment status: {e}")
            return False
    
    def delete_appointment(self, appointment_id: int) -> bool:
        """Delete appointment"""
        try:
            with self.get_session() as session:
                appointment = session.query(Appointment).filter_by(id=appointment_id).first()
                if appointment:
                    session.delete(appointment)
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete appointment: {e}")
            return False
    
    def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """Get appointments that need reminders (tomorrow, not sent yet)"""
        try:
            with self.get_session() as session:
                tomorrow = datetime.now().date() + timedelta(days=1)
                day_after = tomorrow + timedelta(days=1)
                
                appointments = session.query(
                    Appointment, Patient
                ).join(Patient).filter(
                    and_(
                        Appointment.appointment_date >= tomorrow,
                        Appointment.appointment_date < day_after,
                        Appointment.reminder_sent == False,
                        Appointment.status == AppointmentStatus.WAITING
                    )
                ).all()
                
                result = []
                for appt, patient in appointments:
                    result.append({
                        'id': appt.id,
                        'patient_name': encryption_manager.decrypt(patient.full_name),
                        'phone': encryption_manager.decrypt(patient.phone),
                        'email': patient.email,
                        'appointment_date': appt.appointment_date
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch pending reminders: {e}")
            return []
    
    def mark_reminder_sent(self, appointment_id: int = None, reminder_id: int = None) -> bool:
        """Mark reminder as sent"""
        try:
            if appointment_id is None:
                appointment_id = reminder_id
            with self.get_session() as session:
                appointment = session.query(Appointment).filter_by(id=appointment_id).first()
                if appointment:
                    appointment.reminder_sent = True
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to mark reminder sent: {e}")
            return False
    
    # ==================== FINANCIAL MANAGEMENT ====================
    
    def create_transaction(
        self, transaction_type: str, category: str,
        amount: float, description: str, date: datetime = None
    ) -> Tuple[bool, str]:
        """Create financial transaction"""
        try:
            with self.get_session() as session:
                # Convert type string to enum
                try:
                    type_enum = TransactionType[transaction_type.upper()]
                except KeyError:
                    type_enum = TransactionType.INCOME if transaction_type == "Gelir" else TransactionType.EXPENSE
                
                transaction = Transaction(
                    type=type_enum,
                    category=category,
                    amount=amount,
                    description=description,
                    transaction_date=date or datetime.now()
                )
                
                session.add(transaction)
                session.commit()
                
                logger.info(f"Transaction created: {type_enum.value} {amount}")
                return True, "İşlem kaydedildi"
                
        except Exception as e:
            logger.error(f"Transaction creation failed: {e}")
            return False, "İşlem kaydedilemedi"

    def add_transaction(
        self, patient_id: int, amount: float, transaction_type: TransactionType,
        description: str, payment_method: str = "Genel"
    ) -> Optional[int]:
        """Compatibility wrapper for tests to add transactions."""
        try:
            type_enum = transaction_type if isinstance(transaction_type, TransactionType) else TransactionType[str(transaction_type).upper()]
        except KeyError:
            type_enum = TransactionType.INCOME

        try:
            with self.get_session() as session:
                transaction = Transaction(
                    type=type_enum,
                    category=payment_method or "Genel",
                    amount=amount,
                    description=description,
                    transaction_date=datetime.now()
                )
                session.add(transaction)
                session.commit()
                return transaction.id
        except Exception as e:
            logger.error(f"Failed to add transaction: {e}")
            return None

    def get_transactions_for_period(self, start_date: datetime, end_date: datetime) -> List[Transaction]:
        """Get transactions between start and end dates."""
        try:
            with self.get_session() as session:
                transactions = session.query(Transaction).filter(
                    and_(
                        Transaction.transaction_date >= start_date,
                        Transaction.transaction_date <= end_date
                    )
                ).all()
                for transaction in transactions:
                    session.expunge(transaction)
                return transactions
        except Exception as e:
            logger.error(f"Failed to fetch transactions for period: {e}")
            return []
    
    def get_transactions(
        self, start_date: datetime = None, end_date: datetime = None,
        transaction_type: str = None
    ) -> List[Dict[str, Any]]:
        """Get transactions with optional filters"""
        try:
            with self.get_session() as session:
                query = session.query(Transaction)
                
                # Apply filters
                if start_date:
                    query = query.filter(Transaction.transaction_date >= start_date)
                if end_date:
                    query = query.filter(Transaction.transaction_date <= end_date)
                if transaction_type:
                    try:
                        type_enum = TransactionType[transaction_type.upper()]
                        query = query.filter(Transaction.type == type_enum)
                    except KeyError:
                        pass
                
                transactions = query.order_by(Transaction.transaction_date.desc()).all()
                
                result = []
                for t in transactions:
                    result.append({
                        'id': t.id,
                        'type': t.type.value,
                        'category': t.category,
                        'amount': t.amount,
                        'description': t.description,
                        'date': t.transaction_date
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch transactions: {e}")
            return []
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete transaction"""
        try:
            with self.get_session() as session:
                transaction = session.query(Transaction).filter_by(id=transaction_id).first()
                if transaction:
                    session.delete(transaction)
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete transaction: {e}")
            return False
    
    def get_financial_summary(
        self, start_date: datetime = None, end_date: datetime = None
    ) -> Dict[str, float]:
        """Get financial summary (income, expense, net)"""
        try:
            with self.get_session() as session:
                query = session.query(
                    Transaction.type,
                    func.sum(Transaction.amount)
                )
                
                if start_date:
                    query = query.filter(Transaction.transaction_date >= start_date)
                if end_date:
                    query = query.filter(Transaction.transaction_date <= end_date)
                
                results = query.group_by(Transaction.type).all()
                
                income = 0
                expense = 0
                
                for trans_type, total in results:
                    if trans_type == TransactionType.INCOME:
                        income = total or 0
                    elif trans_type == TransactionType.EXPENSE:
                        expense = total or 0
                
                return {
                    'income': income,
                    'expense': expense,
                    'net': income - expense
                }
                
        except Exception as e:
            logger.error(f"Failed to get financial summary: {e}")
            return {'income': 0, 'expense': 0, 'net': 0}
    
    # ==================== INVENTORY MANAGEMENT ====================
    
    def create_product(
        self, name: str, unit: str, quantity: int, threshold: int = 10
    ) -> Tuple[bool, str]:
        """Create inventory product"""
        try:
            with self.get_session() as session:
                product = Product(
                    name=name,
                    unit=unit,
                    quantity=quantity,
                    threshold=threshold
                )
                
                session.add(product)
                session.commit()
                
                logger.info(f"Product created: {name}")
                return True, "Ürün eklendi"
                
        except Exception as e:
            logger.error(f"Product creation failed: {e}")
            return False, "Ürün eklenemedi"
    
    def get_inventory(self) -> List[Dict[str, Any]]:
        """Get all inventory products"""
        try:
            with self.get_session() as session:
                products = session.query(Product).order_by(Product.name).all()
                
                result = []
                for p in products:
                    result.append({
                        'id': p.id,
                        'name': p.name,
                        'unit': p.unit,
                        'quantity': p.quantity,
                        'threshold': p.threshold,
                        'is_low_stock': p.quantity <= p.threshold
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch inventory: {e}")
            return []
    
    def update_product_quantity(
        self, product_id: int, quantity_change: int,
        user_id: int = None, patient_id: int = None
    ) -> bool:
        """Update product quantity and log the change"""
        try:
            with self.get_session() as session:
                product = session.query(Product).filter_by(id=product_id).first()
                if not product:
                    return False
                
                # Update quantity
                product.quantity += quantity_change
                
                # Log the change
                log = InventoryLog(
                    product_id=product_id,
                    user_id=user_id,
                    patient_id=patient_id,
                    quantity=quantity_change
                )
                session.add(log)
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to update product quantity: {e}")
            return False
    
    def delete_product(self, product_id: int) -> bool:
        """Delete product"""
        try:
            with self.get_session() as session:
                product = session.query(Product).filter_by(id=product_id).first()
                if product:
                    session.delete(product)
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete product: {e}")
            return False
    
    # ==================== MESSAGING ====================
    
    def send_message(
        self, sender_id: int, receiver_id: int, message: str
    ) -> bool:
        """Send internal message"""
        try:
            with self.get_session() as session:
                msg = Message(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    message=message
                )
                
                session.add(msg)
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def get_chat_history(
        self, user1_id: int, user2_id: int
    ) -> List[Dict[str, Any]]:
        """Get chat history between two users"""
        try:
            with self.get_session() as session:
                messages = session.query(Message).filter(
                    or_(
                        and_(
                            Message.sender_id == user1_id,
                            Message.receiver_id == user2_id
                        ),
                        and_(
                            Message.sender_id == user2_id,
                            Message.receiver_id == user1_id
                        )
                    )
                ).order_by(Message.created_at).all()
                
                result = []
                for msg in messages:
                    result.append({
                        'sender_id': msg.sender_id,
                        'message': msg.message,
                        'timestamp': msg.created_at,
                        'is_read': msg.is_read
                    })
                
                # Mark messages as read
                session.query(Message).filter(
                    and_(
                        Message.sender_id == user2_id,
                        Message.receiver_id == user1_id,
                        Message.is_read == False
                    )
                ).update({'is_read': True})
                session.commit()
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch chat history: {e}")
            return []
    
    # ==================== SETTINGS ====================
    
    def get_setting(self, key: str) -> Optional[str]:
        """Get setting value"""
        try:
            with self.get_session() as session:
                setting = session.query(Setting).filter_by(key=key).first()
                return setting.value if setting else None
        except Exception as e:
            logger.error(f"Failed to get setting: {e}")
            return None
    
    def set_setting(self, key: str, value: str) -> bool:
        """Set setting value (upsert)"""
        try:
            with self.get_session() as session:
                setting = session.query(Setting).filter_by(key=key).first()
                
                if setting:
                    setting.value = value
                    setting.updated_at = datetime.now()
                else:
                    setting = Setting(key=key, value=value)
                    session.add(setting)
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to set setting: {e}")
            return False
    
    def is_module_active(self, module_key: str) -> bool:
        """Check if module is active"""
        value = self.get_setting(module_key)
        return value == "1"
    
    # ==================== AUDIT LOGGING ====================
    
    def add_audit_log(
        self, user_id: int, action_type: str = None,
        description: str = None, ip_address: str = None,
        action: str = None, details: str = None
    ) -> bool:
        """Add audit log entry"""
        try:
            if action_type is None:
                action_type = action
            if description is None:
                description = details
            with self.get_session() as session:
                log = AuditLog(
                    user_id=user_id,
                    action_type=action_type,
                    description=description,
                    ip_address=ip_address
                )
                
                session.add(log)
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to add audit log: {e}")
            return False
    
    def get_audit_logs(
        self, user_id: int = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit logs"""
        try:
            with self.get_session() as session:
                query = session.query(AuditLog, User).join(
                    User, AuditLog.user_id == User.id, isouter=True
                ).order_by(AuditLog.created_at.desc())
                
                if user_id:
                    query = query.filter(AuditLog.user_id == user_id)
                
                logs = query.limit(limit).all()
                
                result = []
                for log, user in logs:
                    result.append({
                        'id': log.id,
                        'user_name': user.full_name if user else "System",
                        'action_type': log.action_type,
                        'description': log.description,
                        'ip_address': log.ip_address,
                        'timestamp': log.created_at
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch audit logs: {e}")
            return []
    
    # ==================== MEDICAL NEWS ====================
    
    def add_news_article(
        self, title: str, summary: str, link: str,
        source: str, published_date: datetime = None,
        image_url: str = None
    ) -> bool:
        """Add medical news article"""
        try:
            with self.get_session() as session:
                # Check if already exists
                existing = session.query(MedicalNews).filter_by(link=link).first()
                if existing:
                    return False
                
                article = MedicalNews(
                    title=title,
                    summary=summary,
                    link=link,
                    source=source,
                    image_url=image_url,
                    published_date=published_date or datetime.now()
                )
                
                session.add(article)
                session.commit()
                return True
                
        except IntegrityError:
            return False  # Duplicate link
        except Exception as e:
            logger.error(f"Failed to add news article: {e}")
            return False
    
    def get_news_articles(
        self, limit: int = 20, offset: int = 0,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get medical news articles"""
        try:
            with self.get_session() as session:
                query = session.query(MedicalNews)
                
                if unread_only:
                    query = query.filter(MedicalNews.is_read == False)
                
                articles = query.order_by(
                    MedicalNews.published_date.desc()
                ).limit(limit).offset(offset).all()
                
                result = []
                for article in articles:
                    result.append({
                        'id': article.id,
                        'title': article.title,
                        'summary': article.summary,
                        'link': article.link,
                        'source': article.source,
                        'image_url': article.image_url,
                        'is_read': article.is_read,
                        'is_saved': article.is_saved,
                        'published_date': article.published_date
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch news articles: {e}")
            return []
    
    def mark_news_read(self, news_id: int = None, mark_all: bool = False) -> bool:
        """Mark news as read"""
        try:
            with self.get_session() as session:
                if mark_all:
                    session.query(MedicalNews).update({'is_read': True})
                elif news_id:
                    article = session.query(MedicalNews).filter_by(id=news_id).first()
                    if article:
                        article.is_read = True
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to mark news as read: {e}")
            return False
    
    def toggle_news_saved(self, news_id: int) -> bool:
        """Toggle news saved status"""
        try:
            with self.get_session() as session:
                article = session.query(MedicalNews).filter_by(id=news_id).first()
                if article:
                    article.is_saved = not article.is_saved
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to toggle news saved: {e}")
            return False
    
    # ==================== MEDICAL RECORDS ====================
    
    def add_medical_record(
        self, patient_id: int, doctor_id: int,
        anamnez: str, diagnosis: str, treatment: str, prescription: str
    ) -> Tuple[bool, str]:
        """Add medical examination record"""
        try:
            with self.get_session() as session:
                record = MedicalRecord(
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    anamnez=anamnez,
                    diagnosis=diagnosis,
                    treatment=treatment,
                    prescription=prescription
                )
                
                session.add(record)
                session.commit()
                
                logger.info(f"Medical record created for patient {patient_id}")
                return True, "Muayene kaydı oluşturuldu"
                
        except Exception as e:
            logger.error(f"Failed to add medical record: {e}")
            return False, "Kayıt oluşturulamadı"
    
    def get_patient_medical_history(
        self, patient_id: int
    ) -> List[Dict[str, Any]]:
        """Get patient's medical history"""
        try:
            with self.get_session() as session:
                records = session.query(
                    MedicalRecord, User
                ).join(User, MedicalRecord.doctor_id == User.id).filter(
                    MedicalRecord.patient_id == patient_id
                ).order_by(MedicalRecord.record_date.desc()).all()
                
                result = []
                for record, doctor in records:
                    result.append({
                        'id': record.id,
                        'doctor_name': doctor.full_name,
                        'anamnez': record.anamnez,
                        'diagnosis': record.diagnosis,
                        'treatment': record.treatment,
                        'prescription': record.prescription,
                        'date': record.record_date
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch medical history: {e}")
            return []
    
    # ==================== PATIENT FILES ====================
    
    def add_patient_file(
        self, patient_id: int, file_name: str,
        file_path: str, file_type: str, file_size: int = 0
    ) -> bool:
        """Add patient file (X-ray, lab result, etc.)"""
        try:
            with self.get_session() as session:
                file_record = PatientFile(
                    patient_id=patient_id,
                    file_name=file_name,
                    file_path=file_path,
                    file_type=file_type,
                    file_size=file_size
                )
                
                session.add(file_record)
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to add patient file: {e}")
            return False
    
    def get_patient_files(self, patient_id: int) -> List[Dict[str, Any]]:
        """Get patient files"""
        try:
            with self.get_session() as session:
                files = session.query(PatientFile).filter_by(
                    patient_id=patient_id
                ).order_by(PatientFile.upload_date.desc()).all()
                
                result = []
                for f in files:
                    result.append({
                        'id': f.id,
                        'file_name': f.file_name,
                        'file_path': f.file_path,
                        'file_type': f.file_type,
                        'file_size': f.file_size,
                        'upload_date': f.upload_date
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to fetch patient files: {e}")
            return []
    
    # ==================== STATISTICS & DASHBOARD ====================
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            with self.get_session() as session:
                # Today's appointments
                today = datetime.now().date()
                tomorrow = today + timedelta(days=1)
                
                today_appts = session.query(Appointment).filter(
                    and_(
                        Appointment.appointment_date >= today,
                        Appointment.appointment_date < tomorrow
                    )
                ).count()
                
                # Total patients
                total_patients = session.query(Patient).filter(
                    Patient.status != PatientStatus.ARCHIVED
                ).count()
                
                # This month's income
                month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
                month_income = session.query(
                    func.sum(Transaction.amount)
                ).filter(
                    and_(
                        Transaction.type == TransactionType.INCOME,
                        Transaction.transaction_date >= month_start
                    )
                ).scalar() or 0
                
                # Appointment status breakdown
                status_breakdown = session.query(
                    Appointment.status,
                    func.count(Appointment.id)
                ).filter(
                    and_(
                        Appointment.appointment_date >= today,
                        Appointment.appointment_date < tomorrow
                    )
                ).group_by(Appointment.status).all()
                
                return {
                    'today_appointments': today_appts,
                    'total_patients': total_patients,
                    'month_income': month_income,
                    'status_breakdown': [
                        {'status': status.value, 'count': count}
                        for status, count in status_breakdown
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get dashboard stats: {e}")
            return {
                'today_appointments': 0,
                'total_patients': 0,
                'month_income': 0,
                'status_breakdown': []
            }
    
    # ==================== CLEANUP & MAINTENANCE ====================
    
    def cleanup_old_data(self):
        """Clean up old data based on retention policies"""
        try:
            with self.get_session() as session:
                # Clean old news
                retention_days = int(self.get_setting("news_retention_days") or 7)
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                
                session.query(MedicalNews).filter(
                    and_(
                        MedicalNews.published_date < cutoff_date,
                        MedicalNews.is_saved == False
                    )
                ).delete()
                
                session.commit()
                logger.info("Old data cleanup completed")
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Global instance
def get_db_session():
    """Get global database manager instance"""
    return DatabaseManager()


# Singleton instance
_db_instance = None

def get_db() -> DatabaseManager:
    """Get or create database manager singleton"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
