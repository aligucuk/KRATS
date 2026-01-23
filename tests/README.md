# KRATS Test Suite Documentation

## Overview

This directory contains comprehensive tests for the KRATS Clinical Management System. The test suite covers unit tests, integration tests, and security tests to ensure code quality and reliability.

## Test Structure

```
tests/
├── README.md                          # This file
├── conftest.py                        # Pytest configuration and fixtures
├── __init__.py
├── unit/                              # Unit tests
│   ├── test_validators.py            # Validation logic tests
│   ├── test_security_manager.py      # Security and encryption tests
│   ├── test_encryption_manager.py    # Data encryption tests
│   └── test_license_service.py       # License management tests
├── integration/                       # Integration tests
│   ├── test_db_manager.py            # Database operations tests
│   └── test_notification_service.py  # Notification service tests
└── fixtures/                          # Test data and fixtures
    └── __init__.py
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Database tests
pytest -m database

# Security tests
pytest -m security

# Slow tests (excluded by default)
pytest -m slow
```

### Run Tests with Coverage

```bash
# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# View HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Run Tests in Parallel

```bash
# Use pytest-xdist for parallel execution
pytest -n auto
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.database` - Tests requiring database
- `@pytest.mark.security` - Security-related tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.external` - Tests requiring external services

## Test Coverage Goals

| Module | Target Coverage | Current Status |
|--------|----------------|----------------|
| utils/validators.py | 95%+ | ✅ Comprehensive |
| utils/security_manager.py | 100% | ✅ Comprehensive |
| utils/encryption_manager.py | 100% | ✅ Comprehensive |
| services/license_service.py | 90%+ | ✅ Comprehensive |
| database/db_manager.py | 80%+ | ✅ Integration |
| services/notification_service.py | 70%+ | ✅ Integration |

## Test Fixtures

### Available Fixtures

- `db_manager` - Database manager instance with test database
- `db_session` - Fresh database session for each test
- `security_manager` - SecurityManager instance
- `encryption_manager` - EncryptionManager with test key
- `sample_patient_data` - Sample patient data dictionary
- `sample_user_data` - Sample user data dictionary
- `valid_tc_numbers` - List of valid Turkish ID numbers
- `invalid_tc_numbers` - List of invalid Turkish ID numbers
- `valid_turkish_phones` - List of valid Turkish phone numbers
- `mock_smtp_server` - Mocked SMTP server
- `mock_twilio_client` - Mocked Twilio client

### Using Fixtures

```python
def test_example(db_manager, sample_patient_data):
    """Test using fixtures"""
    patient_id = db_manager.add_patient(**sample_patient_data)
    assert patient_id is not None
```

## Writing New Tests

### Test File Naming

- Unit tests: `test_<module_name>.py`
- Integration tests: `test_<feature>_integration.py`
- Place in appropriate directory (unit/ or integration/)

### Test Function Naming

```python
def test_<function_name>_<scenario>():
    """Test description"""
    # Arrange
    # Act
    # Assert
```

### Example Test Structure

```python
"""
Module docstring describing what is tested
"""
import pytest
from module import ClassToTest


class TestFeatureName:
    """Test suite for specific feature"""

    def test_basic_functionality(self):
        """Test basic operation"""
        # Arrange
        instance = ClassToTest()

        # Act
        result = instance.method()

        # Assert
        assert result is not None

    def test_error_handling(self):
        """Test error conditions"""
        instance = ClassToTest()

        with pytest.raises(ValueError):
            instance.method(invalid_input)
```

## Continuous Integration

Tests run automatically on:

- Push to main/master/develop branches
- Pull requests
- Push to branches starting with "claude/"

### GitHub Actions Workflows

- **tests.yml** - Main test suite
  - Runs tests on Python 3.10, 3.11, 3.12
  - Generates coverage reports
  - Uploads to Codecov
- **Security checks** - Bandit and safety scans
- **Linting** - Flake8, pylint, mypy, isort

## Pre-commit Hooks

Install pre-commit hooks to run tests before committing:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

Hooks include:
- Black (code formatting)
- isort (import sorting)
- flake8 (linting)
- bandit (security)
- Trailing whitespace removal
- Private key detection
- Pytest (on push only)

## Test Data

### Turkish ID (TC) Numbers

Test uses algorithmically valid TC numbers for validation:
- `10000000146` - Valid
- `10000000278` - Valid
- `00000000000` - Invalid (starts with 0)
- `12345678901` - Invalid (wrong checksum)

### Patient Data

Sample patient data available in fixtures:
```python
{
    "tc_no": "12345678901",
    "first_name": "Ahmet",
    "last_name": "Yılmaz",
    "phone": "5551234567",
    "email": "ahmet.yilmaz@example.com",
    "birth_date": "01/01/1990",
    "address": "İstanbul, Türkiye",
    "gender": "Erkek"
}
```

## Debugging Tests

### Run Tests with Verbose Output

```bash
pytest -vv
```

### Show Print Statements

```bash
pytest -s
```

### Stop at First Failure

```bash
pytest -x
```

### Run Specific Test

```bash
# By test name
pytest tests/unit/test_validators.py::TestTCValidation::test_valid_tc_numbers

# By keyword
pytest -k "test_valid"
```

### Debug with pdb

```python
def test_example():
    import pdb; pdb.set_trace()
    # Your test code
```

Or use pytest's built-in debugger:

```bash
pytest --pdb
```

## Common Issues

### Import Errors

Ensure PYTHONPATH includes project root:

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest
```

### Database Lock Errors (SQLite)

SQLite may lock during tests. Use separate test database:

```bash
# Tests automatically use in-memory or temporary database
pytest
```

### Missing Dependencies

Install all dev dependencies:

```bash
pip install -r requirements-dev.txt
```

## Test Metrics

### Current Coverage

Run to see current coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

### Coverage Goals

- **Critical modules** (security, encryption): 100%
- **Core business logic** (validators, db_manager): 80%+
- **Services**: 70%+
- **UI**: 60%+
- **Overall project**: 70%+

## Contributing Tests

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all tests pass: `pytest`
3. Check coverage: `pytest --cov`
4. Run pre-commit checks: `pre-commit run --all-files`
5. Update this documentation if needed

## Security Testing

### Running Security Tests

```bash
# Bandit security scan
bandit -r . --exclude './venv,./tests'

# Check for known vulnerabilities
pip freeze | safety check --stdin
```

### Security Test Categories

- Password hashing and verification
- Data encryption/decryption
- SQL injection prevention
- XSS attack handling
- License key validation
- Audit logging

## Performance Testing

Slow tests are marked with `@pytest.mark.slow`:

```bash
# Run all tests including slow ones
pytest -m slow

# Skip slow tests (default)
pytest -m "not slow"
```

## Need Help?

- Check pytest documentation: https://docs.pytest.org/
- Review existing tests for examples
- Ask in team chat or create an issue

## Test Statistics

- **Total Test Files**: 6
- **Unit Tests**: 4 files
- **Integration Tests**: 2 files
- **Total Test Cases**: 200+ tests
- **Coverage Target**: 70%+ overall
- **CI/CD**: Automated on every push
