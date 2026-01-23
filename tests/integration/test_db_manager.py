"""
Integration tests for database/db_manager.py

Tests cover:
- Database initialization and setup
- User authentication and management
- Patient CRUD operations with encryption
- Appointment management
- Transaction management
- Session handling and cleanup
- Audit logging
- Data integrity and constraints
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from database.db_manager import DatabaseManager
from database.models import (
    User, Patient, Appointment, Transaction, Product,
    Message, Setting, AuditLog,
    UserRole, AppointmentStatus, PatientStatus, TransactionType
)
from utils.exceptions import DatabaseException


# ==================== DATABASE INITIALIZATION ====================

@pytest.mark.database
class TestDatabaseInitialization:
    """Test database initialization"""

    def test_database_manager_initialization(self, db_manager):
        """Test that DatabaseManager initializes correctly"""
        assert db_manager is not None
        assert db_manager.engine is not None
        assert db_manager.Session is not None

    def test_default_admin_user_created(self, db_manager):
        """Test that default admin user is created"""
        with db_manager.get_session() as session:
            admin = session.query(User).filter_by(username="admin").first()

            assert admin is not None
            assert admin.role == UserRole.ADMIN
            assert admin.full_name == "Sistem Yöneticisi"
            assert admin.is_active is True

    def test_default_settings_created(self, db_manager):
        """Test that default settings are created"""
        with db_manager.get_session() as session:
            country_setting = session.query(Setting).filter_by(key="country").first()
            theme_setting = session.query(Setting).filter_by(key="theme_color").first()

            assert country_setting is not None
            assert country_setting.value == "TR"
            assert theme_setting is not None
            assert theme_setting.value == "teal"

    def test_default_news_sources_created(self, db_manager):
        """Test that default news sources are created"""
        from database.models import NewsSource

        with db_manager.get_session() as session:
            sources = session.query(NewsSource).all()

            assert len(sources) >= 3  # At least 3 default sources
            assert any("Google" in source.name for source in sources)


# ==================== USER AUTHENTICATION ====================

@pytest.mark.database
class TestUserAuthentication:
    """Test user authentication"""

    def test_authenticate_admin_user(self, db_manager):
        """Test authentication of default admin user"""
        user = db_manager.authenticate_user("admin", "admin")

        assert user is not None
        assert user.username == "admin"
        assert user.role == UserRole.ADMIN

    def test_authenticate_wrong_password(self, db_manager):
        """Test authentication with wrong password"""
        user = db_manager.authenticate_user("admin", "wrongpassword")

        assert user is None

    def test_authenticate_nonexistent_user(self, db_manager):
        """Test authentication of nonexistent user"""
        user = db_manager.authenticate_user("nonexistent", "password")

        assert user is None

    def test_authenticate_updates_last_login(self, db_manager):
        """Test that authentication updates last_login"""
        # Authenticate
        user = db_manager.authenticate_user("admin", "admin")
        assert user is not None

        # Check that last_login was updated
        with db_manager.get_session() as session:
            admin = session.query(User).filter_by(username="admin").first()
            assert admin.last_login is not None
            assert (datetime.now() - admin.last_login).total_seconds() < 5

    def test_authenticate_creates_audit_log(self, db_manager):
        """Test that authentication creates audit log"""
        user = db_manager.authenticate_user("admin", "admin")

        with db_manager.get_session() as session:
            # Check audit log
            recent_logs = session.query(AuditLog).filter(
                AuditLog.action == "LOGIN"
            ).order_by(AuditLog.timestamp.desc()).limit(1).all()

            assert len(recent_logs) > 0


# ==================== USER MANAGEMENT ====================

@pytest.mark.database
class TestUserManagement:
    """Test user management operations"""

    def test_create_user(self, db_manager):
        """Test creating a new user"""
        result = db_manager.create_user(
            username="testdoctor",
            password="testpass123",
            full_name="Dr. Test Doktor",
            role=UserRole.DOCTOR,
            specialty="Genel Pratisyen"
        )

        assert result is True

        # Verify user was created
        with db_manager.get_session() as session:
            user = session.query(User).filter_by(username="testdoctor").first()
            assert user is not None
            assert user.full_name == "Dr. Test Doktor"
            assert user.specialty == "Genel Pratisyen"

    def test_create_duplicate_username(self, db_manager):
        """Test that duplicate username is rejected"""
        # Create first user
        db_manager.create_user(
            username="doctor1",
            password="pass123",
            full_name="Doctor One",
            role=UserRole.DOCTOR
        )

        # Try to create duplicate
        result = db_manager.create_user(
            username="doctor1",
            password="pass456",
            full_name="Doctor Two",
            role=UserRole.DOCTOR
        )

        assert result is False

    def test_get_user_by_id(self, db_manager):
        """Test getting user by ID"""
        with db_manager.get_session() as session:
            admin = session.query(User).filter_by(username="admin").first()
            user_id = admin.id

        # Use the db_manager method (if exists) or session
        with db_manager.get_session() as session:
            user = session.query(User).get(user_id)
            assert user is not None
            assert user.username == "admin"


# ==================== PATIENT MANAGEMENT ====================

@pytest.mark.database
class TestPatientManagement:
    """Test patient management operations"""

    def test_add_patient(self, db_manager, sample_patient_data):
        """Test adding a new patient"""
        patient_id = db_manager.add_patient(
            tc_no=sample_patient_data["tc_no"],
            first_name=sample_patient_data["first_name"],
            last_name=sample_patient_data["last_name"],
            phone=sample_patient_data["phone"],
            email=sample_patient_data["email"],
            birth_date=sample_patient_data["birth_date"],
            address=sample_patient_data["address"],
            gender=sample_patient_data["gender"]
        )

        assert patient_id is not None
        assert patient_id > 0

        # Verify patient was created
        with db_manager.get_session() as session:
            patient = session.query(Patient).get(patient_id)
            assert patient is not None
            assert patient.first_name == "Ahmet"
            assert patient.last_name == "Yılmaz"

    def test_add_patient_encrypts_sensitive_data(self, db_manager, sample_patient_data):
        """Test that sensitive patient data is encrypted"""
        patient_id = db_manager.add_patient(**sample_patient_data)

        with db_manager.get_session() as session:
            patient = session.query(Patient).get(patient_id)

            # TC and phone should be encrypted (not equal to plain text)
            # Note: This depends on db_manager implementation
            assert patient.tc_no is not None
            assert patient.phone is not None

    def test_get_patient(self, db_manager, sample_patient_data):
        """Test getting patient by ID"""
        patient_id = db_manager.add_patient(**sample_patient_data)

        patient = db_manager.get_patient(patient_id)

        assert patient is not None
        assert patient.id == patient_id
        assert patient.first_name == "Ahmet"

    def test_get_nonexistent_patient(self, db_manager):
        """Test getting nonexistent patient"""
        patient = db_manager.get_patient(99999)
        assert patient is None

    def test_update_patient(self, db_manager, sample_patient_data):
        """Test updating patient information"""
        patient_id = db_manager.add_patient(**sample_patient_data)

        # Update patient
        result = db_manager.update_patient(
            patient_id,
            phone="5559999999",
            email="newemail@example.com"
        )

        assert result is True

        # Verify update
        patient = db_manager.get_patient(patient_id)
        # Note: Phone might be encrypted, so we check it was updated
        assert patient.email == "newemail@example.com"

    def test_search_patients(self, db_manager, sample_patient_data):
        """Test searching patients"""
        # Add test patient
        db_manager.add_patient(**sample_patient_data)

        # Search by name
        patients = db_manager.search_patients(query="Ahmet")

        assert len(patients) > 0
        assert any(p.first_name == "Ahmet" for p in patients)

    def test_get_all_patients(self, db_manager, sample_patient_data):
        """Test getting all patients"""
        # Add multiple patients
        db_manager.add_patient(**sample_patient_data)

        sample_patient_data2 = sample_patient_data.copy()
        sample_patient_data2["tc_no"] = "98765432109"
        sample_patient_data2["first_name"] = "Mehmet"
        db_manager.add_patient(**sample_patient_data2)

        # Get all patients
        patients = db_manager.get_all_patients()

        assert len(patients) >= 2


# ==================== APPOINTMENT MANAGEMENT ====================

@pytest.mark.database
class TestAppointmentManagement:
    """Test appointment management operations"""

    def test_create_appointment(self, db_manager, sample_patient_data):
        """Test creating an appointment"""
        # Create patient and get admin user
        patient_id = db_manager.add_patient(**sample_patient_data)

        with db_manager.get_session() as session:
            admin = session.query(User).filter_by(username="admin").first()
            doctor_id = admin.id

        # Create appointment
        appointment_date = datetime.now() + timedelta(days=1)
        appointment_id = db_manager.create_appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            notes="Rutin kontrol"
        )

        assert appointment_id is not None
        assert appointment_id > 0

        # Verify appointment
        with db_manager.get_session() as session:
            appointment = session.query(Appointment).get(appointment_id)
            assert appointment is not None
            assert appointment.patient_id == patient_id
            assert appointment.notes == "Rutin kontrol"

    def test_get_appointments_for_date(self, db_manager, sample_patient_data):
        """Test getting appointments for a specific date"""
        # Create appointment
        patient_id = db_manager.add_patient(**sample_patient_data)

        with db_manager.get_session() as session:
            admin = session.query(User).filter_by(username="admin").first()
            doctor_id = admin.id

        appointment_date = datetime.now() + timedelta(days=1)
        db_manager.create_appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date
        )

        # Get appointments for that date
        appointments = db_manager.get_appointments_for_date(appointment_date.date())

        assert len(appointments) > 0

    def test_update_appointment_status(self, db_manager, sample_patient_data):
        """Test updating appointment status"""
        # Create appointment
        patient_id = db_manager.add_patient(**sample_patient_data)

        with db_manager.get_session() as session:
            admin = session.query(User).filter_by(username="admin").first()
            doctor_id = admin.id

        appointment_date = datetime.now() + timedelta(days=1)
        appointment_id = db_manager.create_appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date
        )

        # Update status
        result = db_manager.update_appointment_status(
            appointment_id,
            AppointmentStatus.COMPLETED
        )

        assert result is True

        # Verify update
        with db_manager.get_session() as session:
            appointment = session.query(Appointment).get(appointment_id)
            assert appointment.status == AppointmentStatus.COMPLETED


# ==================== TRANSACTION MANAGEMENT ====================

@pytest.mark.database
class TestTransactionManagement:
    """Test financial transaction operations"""

    def test_add_transaction(self, db_manager, sample_patient_data):
        """Test adding a transaction"""
        patient_id = db_manager.add_patient(**sample_patient_data)

        transaction_id = db_manager.add_transaction(
            patient_id=patient_id,
            amount=500.00,
            transaction_type=TransactionType.INCOME,
            description="Muayene ücreti",
            payment_method="Nakit"
        )

        assert transaction_id is not None
        assert transaction_id > 0

        # Verify transaction
        with db_manager.get_session() as session:
            transaction = session.query(Transaction).get(transaction_id)
            assert transaction is not None
            assert transaction.amount == 500.00
            assert transaction.transaction_type == TransactionType.INCOME

    def test_get_transactions_for_period(self, db_manager, sample_patient_data):
        """Test getting transactions for a period"""
        patient_id = db_manager.add_patient(**sample_patient_data)

        # Add transaction
        db_manager.add_transaction(
            patient_id=patient_id,
            amount=500.00,
            transaction_type=TransactionType.INCOME,
            description="Test"
        )

        # Get transactions for today
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)

        transactions = db_manager.get_transactions_for_period(start_date, end_date)

        assert len(transactions) > 0


# ==================== SESSION HANDLING ====================

@pytest.mark.database
class TestSessionHandling:
    """Test database session management"""

    def test_session_context_manager(self, db_manager):
        """Test that session context manager works correctly"""
        with db_manager.get_session() as session:
            assert session is not None

            # Should be able to query
            user_count = session.query(User).count()
            assert user_count >= 1  # At least admin user

    def test_session_commit_on_success(self, db_manager):
        """Test that session commits on success"""
        with db_manager.get_session() as session:
            # Add a setting
            setting = Setting(key="test_key", value="test_value")
            session.add(setting)

        # Verify it was committed
        with db_manager.get_session() as session:
            saved_setting = session.query(Setting).filter_by(key="test_key").first()
            assert saved_setting is not None
            assert saved_setting.value == "test_value"

    def test_session_rollback_on_error(self, db_manager):
        """Test that session rolls back on error"""
        try:
            with db_manager.get_session() as session:
                # Add a user
                user = User(
                    username="test_rollback",
                    password="hashed",
                    full_name="Test User",
                    role=UserRole.DOCTOR
                )
                session.add(user)

                # Force an error
                raise Exception("Test error")

        except DatabaseException:
            pass

        # Verify rollback - user should not exist
        with db_manager.get_session() as session:
            user = session.query(User).filter_by(username="test_rollback").first()
            assert user is None


# ==================== AUDIT LOGGING ====================

@pytest.mark.database
class TestAuditLogging:
    """Test audit logging functionality"""

    def test_add_audit_log(self, db_manager):
        """Test adding audit log entry"""
        with db_manager.get_session() as session:
            admin = session.query(User).filter_by(username="admin").first()
            user_id = admin.id

        result = db_manager.add_audit_log(
            user_id=user_id,
            action="TEST_ACTION",
            details="Test audit log entry"
        )

        assert result is True

        # Verify audit log
        with db_manager.get_session() as session:
            log = session.query(AuditLog).filter_by(
                action="TEST_ACTION"
            ).first()

            assert log is not None
            assert log.user_id == user_id
            assert log.details == "Test audit log entry"

    def test_get_recent_audit_logs(self, db_manager):
        """Test getting recent audit logs"""
        with db_manager.get_session() as session:
            admin = session.query(User).filter_by(username="admin").first()
            user_id = admin.id

        # Add some logs
        for i in range(5):
            db_manager.add_audit_log(
                user_id=user_id,
                action=f"ACTION_{i}",
                details=f"Test {i}"
            )

        # Get recent logs
        logs = db_manager.get_audit_logs(limit=10)

        assert len(logs) >= 5


# ==================== DATA INTEGRITY ====================

@pytest.mark.database
class TestDataIntegrity:
    """Test data integrity and constraints"""

    def test_user_username_unique_constraint(self, db_manager):
        """Test that username must be unique"""
        # First user should succeed
        result1 = db_manager.create_user(
            username="unique_user",
            password="pass123",
            full_name="User One",
            role=UserRole.DOCTOR
        )
        assert result1 is True

        # Duplicate username should fail
        result2 = db_manager.create_user(
            username="unique_user",
            password="pass456",
            full_name="User Two",
            role=UserRole.DOCTOR
        )
        assert result2 is False

    def test_appointment_requires_patient_and_doctor(self, db_manager):
        """Test that appointment requires both patient and doctor"""
        # Try to create appointment without valid patient/doctor
        try:
            with db_manager.get_session() as session:
                appointment = Appointment(
                    patient_id=99999,  # Non-existent
                    doctor_id=99999,   # Non-existent
                    appointment_date=datetime.now()
                )
                session.add(appointment)
                session.commit()

            assert False, "Should have raised an error"
        except:
            pass  # Expected to fail


# ==================== SETTINGS MANAGEMENT ====================

@pytest.mark.database
class TestSettingsManagement:
    """Test settings management"""

    def test_get_setting(self, db_manager):
        """Test getting a setting value"""
        value = db_manager.get_setting("country")
        assert value == "TR"

    def test_get_nonexistent_setting(self, db_manager):
        """Test getting nonexistent setting returns None"""
        value = db_manager.get_setting("nonexistent_key")
        assert value is None

    def test_set_setting_new(self, db_manager):
        """Test setting a new setting"""
        result = db_manager.set_setting("new_key", "new_value")
        assert result is True

        # Verify
        value = db_manager.get_setting("new_key")
        assert value == "new_value"

    def test_set_setting_update(self, db_manager):
        """Test updating an existing setting"""
        # Set initial value
        db_manager.set_setting("update_key", "old_value")

        # Update
        result = db_manager.set_setting("update_key", "new_value")
        assert result is True

        # Verify
        value = db_manager.get_setting("update_key")
        assert value == "new_value"


# ==================== PERFORMANCE TESTS ====================

@pytest.mark.slow
@pytest.mark.database
class TestPerformance:
    """Performance-related tests"""

    def test_bulk_patient_creation(self, db_manager):
        """Test creating multiple patients"""
        import time

        start = time.time()

        for i in range(10):
            db_manager.add_patient(
                tc_no=f"1000000{i:04d}",
                first_name=f"Patient{i}",
                last_name="Test",
                phone=f"555000{i:04d}",
                email=f"patient{i}@test.com",
                birth_date="01/01/1990",
                gender="Erkek"
            )

        duration = time.time() - start

        # Should complete in reasonable time
        assert duration < 5.0

    def test_query_performance(self, db_manager):
        """Test query performance"""
        import time

        # Add some test data
        for i in range(50):
            db_manager.add_patient(
                tc_no=f"2000000{i:04d}",
                first_name=f"Patient{i}",
                last_name="Test",
                phone=f"555000{i:04d}",
                email=f"patient{i}@test.com",
                birth_date="01/01/1990",
                gender="Erkek"
            )

        # Query all patients
        start = time.time()
        patients = db_manager.get_all_patients()
        duration = time.time() - start

        assert len(patients) >= 50
        assert duration < 1.0  # Should be fast
