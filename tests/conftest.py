"""
Pytest configuration and shared fixtures for KRATS test suite
"""
import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from unittest.mock import patch

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.models import Base
from database.db_manager import DatabaseManager
from utils.security_manager import SecurityManager
from utils.encryption_manager import EncryptionManager
from cryptography.fernet import Fernet


# ==================== PYTEST CONFIGURATION ====================

def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "security: Security-related tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "database: Tests requiring database")
    config.addinivalue_line("markers", "external: Tests requiring external services")


def pytest_addoption(parser):
    """Register coverage options when pytest-cov is unavailable."""
    if importlib.util.find_spec("pytest_cov") is not None:
        return

    group = parser.getgroup("coverage", "coverage reporting")
    group.addoption(
        "--cov",
        action="append",
        dest="cov_source",
        default=[],
        help="(stub) Coverage source paths.",
    )
    group.addoption(
        "--cov-report",
        action="append",
        dest="cov_report",
        default=[],
        help="(stub) Coverage report type.",
    )
    group.addoption(
        "--cov-fail-under",
        action="store",
        dest="cov_fail_under",
        default=None,
        type=int,
        help="(stub) Coverage threshold.",
    )


@pytest.fixture
def mocker():
    """Fallback mocker fixture when pytest-mock is unavailable."""
    class _Mocker:
        def __init__(self):
            self._patches = []

        def patch(self, target, *args, **kwargs):
            patcher = patch(target, *args, **kwargs)
            mocked = patcher.start()
            self._patches.append(patcher)
            return mocked

        def stopall(self):
            for patcher in reversed(self._patches):
                patcher.stop()
            self._patches = []

    manager = _Mocker()
    try:
        yield manager
    finally:
        manager.stopall()


# ==================== DATABASE FIXTURES ====================

@pytest.fixture(scope="session")
def test_db_path():
    """Create a temporary database file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture(scope="session")
def test_engine(test_db_path):
    """Create a test database engine"""
    engine = create_engine(
        f'sqlite:///{test_db_path}',
        connect_args={"check_same_thread": False},
        echo=False
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a fresh database session for each test"""
    connection = test_engine.connect()
    transaction = connection.begin()

    Session = scoped_session(sessionmaker(bind=connection))
    session = Session()

    yield session

    session.close()
    Session.remove()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def db_manager(monkeypatch, test_db_path):
    """Create a DatabaseManager instance with test database"""
    # Monkeypatch the settings to use test database
    import config
    monkeypatch.setattr(config.settings, 'DATABASE_URL', f'sqlite:///{test_db_path}')

    db = DatabaseManager()
    yield db

    # Cleanup
    if hasattr(db, 'engine'):
        db.engine.dispose()


# ==================== SECURITY FIXTURES ====================

@pytest.fixture(scope="session")
def test_encryption_key():
    """Generate a test encryption key"""
    return Fernet.generate_key()


@pytest.fixture(scope="function")
def security_manager():
    """Create a SecurityManager instance for testing"""
    return SecurityManager()


@pytest.fixture(scope="function")
def encryption_manager(test_encryption_key):
    """Create an EncryptionManager instance with test key"""
    return EncryptionManager(key=test_encryption_key.decode())


# ==================== SAMPLE DATA FIXTURES ====================

@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing"""
    return {
        "tc_no": "12345678901",  # Mock valid TC number
        "first_name": "Ahmet",
        "last_name": "Yılmaz",
        "phone": "5551234567",
        "email": "ahmet.yilmaz@example.com",
        "birth_date": "01/01/1990",
        "address": "İstanbul, Türkiye",
        "gender": "Erkek"
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testdoctor",
        "password": "testpass123",
        "full_name": "Dr. Test Doktor",
        "role": "DOCTOR",
        "specialty": "Genel Pratisyen",
        "email": "test.doctor@clinic.com"
    }


@pytest.fixture
def sample_appointment_data():
    """Sample appointment data for testing"""
    return {
        "patient_id": 1,
        "doctor_id": 1,
        "appointment_date": datetime.now() + timedelta(days=1),
        "notes": "Rutin kontrol"
    }


@pytest.fixture
def valid_tc_numbers():
    """List of valid Turkish ID numbers for testing"""
    return [
        "10000000146",
        "10000000278",
        "10000000369",
        "10000000575"
    ]


@pytest.fixture
def invalid_tc_numbers():
    """List of invalid Turkish ID numbers for testing"""
    return [
        "00000000000",  # Starts with 0
        "123456",  # Too short
        "123456789012",  # Too long
        "12345678900",  # Invalid checksum
        "1234567890X"  # Non-numeric
    ]


@pytest.fixture
def valid_turkish_phones():
    """List of valid Turkish phone numbers"""
    return [
        "5551234567",
        "5321234567",
        "905551234567",
        "905321234567",
        "555 123 45 67",
        "+90 555 123 45 67"
    ]


@pytest.fixture
def invalid_turkish_phones():
    """List of invalid Turkish phone numbers"""
    return [
        "4551234567",  # Doesn't start with 5
        "555123",  # Too short
        "555123456789",  # Too long
        "1234567890"  # Wrong format
    ]


# ==================== MOCK FIXTURES ====================

@pytest.fixture
def mock_smtp_server(mocker):
    """Mock SMTP server for email testing"""
    return mocker.patch('smtplib.SMTP')


@pytest.fixture
def mock_twilio_client(mocker):
    """Mock Twilio client for SMS testing"""
    return mocker.patch('services.sms_service.Client')


@pytest.fixture
def mock_selenium_driver(mocker):
    """Mock Selenium driver for WhatsApp testing"""
    return mocker.patch('selenium.webdriver.Chrome')


# ==================== ENVIRONMENT FIXTURES ====================

@pytest.fixture(scope="function")
def clean_environment(monkeypatch):
    """Ensure clean environment variables for testing"""
    # Remove potentially conflicting env vars
    vars_to_remove = [
        'CLINIC_APP_SECRET_KEY',
        'ENCRYPTION_KEY',
        'DATABASE_URL'
    ]
    for var in vars_to_remove:
        monkeypatch.delenv(var, raising=False)

    yield


@pytest.fixture(scope="function")
def temp_secret_key_file():
    """Create a temporary secret.key file"""
    key = Fernet.generate_key()
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.key', delete=False) as f:
        f.write(key)
        key_path = f.name

    yield key_path, key

    # Cleanup
    if os.path.exists(key_path):
        os.unlink(key_path)


# ==================== TIME FIXTURES ====================

@pytest.fixture
def frozen_time():
    """Freeze time for testing time-dependent operations"""
    from freezegun import freeze_time
    freezer = freeze_time("2024-01-15 10:00:00")
    freezer.start()
    yield datetime(2024, 1, 15, 10, 0, 0)
    freezer.stop()


# ==================== HELPER FUNCTIONS ====================

def create_test_patient(session, **kwargs):
    """Helper to create a test patient"""
    from database.models import Patient, PatientStatus

    defaults = {
        "tc_no": "encrypted_tc",
        "first_name": "Test",
        "last_name": "Patient",
        "phone": "encrypted_phone",
        "status": PatientStatus.ACTIVE
    }
    defaults.update(kwargs)

    patient = Patient(**defaults)
    session.add(patient)
    session.commit()
    return patient


def create_test_user(session, **kwargs):
    """Helper to create a test user"""
    from database.models import User, UserRole

    defaults = {
        "username": "testuser",
        "password": "hashed_password",
        "full_name": "Test User",
        "role": UserRole.DOCTOR,
        "specialty": "Test"
    }
    defaults.update(kwargs)

    user = User(**defaults)
    session.add(user)
    session.commit()
    return user
