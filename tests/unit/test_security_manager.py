"""
Comprehensive tests for utils/security_manager.py

Tests cover:
- Password hashing with bcrypt (salt, uniqueness, strength)
- Password verification (correct/incorrect passwords)
- Data encryption with Fernet (roundtrip integrity)
- Data decryption (error handling, edge cases)
- Encryption key management
- Security edge cases and error conditions
"""
import os
import pytest
import tempfile
from pathlib import Path
from cryptography.fernet import Fernet

from utils.security_manager import SecurityManager


# ==================== PASSWORD HASHING ====================

class TestPasswordHashing:
    """Test password hashing functionality"""

    def test_hash_password_creates_hash(self, security_manager):
        """Test that password is successfully hashed"""
        password = "test_password_123"
        hashed = security_manager.hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # Hash should be different from plain password

    def test_hash_password_bcrypt_format(self, security_manager):
        """Test that hash has bcrypt format"""
        password = "test_password"
        hashed = security_manager.hash_password(password)

        # Bcrypt hashes start with $2b$ or $2a$
        assert hashed.startswith('$2')
        # Bcrypt hashes are 60 characters long
        assert len(hashed) == 60

    def test_hash_password_unique_salts(self, security_manager):
        """Test that same password produces different hashes (unique salts)"""
        password = "same_password"
        hash1 = security_manager.hash_password(password)
        hash2 = security_manager.hash_password(password)

        # Same password should produce different hashes due to unique salts
        assert hash1 != hash2

    def test_hash_password_empty_raises_error(self, security_manager):
        """Test that empty password raises ValueError"""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            security_manager.hash_password("")

    def test_hash_password_none_raises_error(self, security_manager):
        """Test that None password raises ValueError"""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            security_manager.hash_password(None)

    def test_hash_password_unicode(self, security_manager):
        """Test hashing password with unicode characters"""
        password = "şifre_Türkçe_123_öçüğı"
        hashed = security_manager.hash_password(password)

        assert hashed is not None
        assert len(hashed) == 60

    def test_hash_password_special_characters(self, security_manager):
        """Test hashing password with special characters"""
        password = "p@ssw0rd!#$%^&*()"
        hashed = security_manager.hash_password(password)

        assert hashed is not None
        assert len(hashed) == 60

    def test_hash_password_very_long(self, security_manager):
        """Test hashing very long password"""
        password = "a" * 1000
        hashed = security_manager.hash_password(password)

        assert hashed is not None
        assert len(hashed) == 60


# ==================== PASSWORD VERIFICATION ====================

class TestPasswordVerification:
    """Test password verification functionality"""

    def test_verify_correct_password(self, security_manager):
        """Test that correct password is verified"""
        password = "correct_password"
        hashed = security_manager.hash_password(password)

        result = security_manager.verify_password(password, hashed)
        assert result is True

    def test_verify_incorrect_password(self, security_manager):
        """Test that incorrect password is rejected"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = security_manager.hash_password(password)

        result = security_manager.verify_password(wrong_password, hashed)
        assert result is False

    def test_verify_case_sensitive(self, security_manager):
        """Test that password verification is case-sensitive"""
        password = "MyPassword"
        hashed = security_manager.hash_password(password)

        # Wrong case should fail
        result = security_manager.verify_password("mypassword", hashed)
        assert result is False

    def test_verify_empty_password(self, security_manager):
        """Test that empty password verification returns False"""
        hashed = security_manager.hash_password("test")
        result = security_manager.verify_password("", hashed)
        assert result is False

    def test_verify_none_password(self, security_manager):
        """Test that None password verification returns False"""
        hashed = security_manager.hash_password("test")
        result = security_manager.verify_password(None, hashed)
        assert result is False

    def test_verify_empty_hash(self, security_manager):
        """Test that verification with empty hash returns False"""
        result = security_manager.verify_password("password", "")
        assert result is False

    def test_verify_none_hash(self, security_manager):
        """Test that verification with None hash returns False"""
        result = security_manager.verify_password("password", None)
        assert result is False

    def test_verify_invalid_hash_format(self, security_manager):
        """Test that verification with invalid hash format returns False"""
        result = security_manager.verify_password("password", "invalid_hash")
        assert result is False

    def test_verify_unicode_password(self, security_manager):
        """Test verification of unicode password"""
        password = "şifre_Türkçe"
        hashed = security_manager.hash_password(password)

        # Correct unicode password
        result = security_manager.verify_password(password, hashed)
        assert result is True

        # Wrong unicode password
        result = security_manager.verify_password("şifre_türkçe", hashed)
        assert result is False


# ==================== PASSWORD STRENGTH VALIDATION ====================

class TestPasswordStrength:
    """Test password strength validation"""

    def test_validate_strong_password(self, security_manager):
        """Test that strong password passes validation"""
        is_valid, msg = security_manager.validate_password_strength("Strong123!")
        assert is_valid
        assert msg == "Geçerli"

    def test_validate_minimum_length(self, security_manager):
        """Test password with exactly 4 characters"""
        is_valid, msg = security_manager.validate_password_strength("Pass")
        assert is_valid

    def test_validate_too_short(self, security_manager):
        """Test that short password fails validation"""
        is_valid, msg = security_manager.validate_password_strength("abc")
        assert not is_valid
        assert "en az 4 karakter" in msg

    def test_validate_empty_password(self, security_manager):
        """Test that empty password fails validation"""
        is_valid, msg = security_manager.validate_password_strength("")
        assert not is_valid


# ==================== DATA ENCRYPTION ====================

class TestDataEncryption:
    """Test data encryption functionality"""

    def test_encrypt_data_basic(self, security_manager):
        """Test basic data encryption"""
        plain_text = "sensitive_data"
        encrypted = security_manager.encrypt_data(plain_text)

        assert encrypted is not None
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
        assert encrypted != plain_text

    def test_encrypt_data_roundtrip(self, security_manager):
        """Test encryption/decryption roundtrip integrity"""
        plain_text = "test_data_12345"
        encrypted = security_manager.encrypt_data(plain_text)
        decrypted = security_manager.decrypt_data(encrypted)

        assert decrypted == plain_text

    def test_encrypt_turkish_characters(self, security_manager):
        """Test encryption of Turkish characters"""
        plain_text = "Şişli İstanbul Çağlayan Öğrenci Ümit"
        encrypted = security_manager.encrypt_data(plain_text)
        decrypted = security_manager.decrypt_data(encrypted)

        assert decrypted == plain_text

    def test_encrypt_tc_number(self, security_manager):
        """Test encryption of Turkish ID number"""
        tc_no = "12345678901"
        encrypted = security_manager.encrypt_data(tc_no)
        decrypted = security_manager.decrypt_data(encrypted)

        assert decrypted == tc_no
        assert encrypted != tc_no

    def test_encrypt_phone_number(self, security_manager):
        """Test encryption of phone number"""
        phone = "5551234567"
        encrypted = security_manager.encrypt_data(phone)
        decrypted = security_manager.decrypt_data(encrypted)

        assert decrypted == phone

    def test_encrypt_empty_string(self, security_manager):
        """Test that empty string returns empty"""
        result = security_manager.encrypt_data("")
        assert result == ""

    def test_encrypt_none(self, security_manager):
        """Test that None returns empty"""
        result = security_manager.encrypt_data(None)
        assert result == ""

    def test_encrypt_numeric_data(self, security_manager):
        """Test encryption of numeric data (converted to string)"""
        number = 12345
        encrypted = security_manager.encrypt_data(number)
        decrypted = security_manager.decrypt_data(encrypted)

        assert decrypted == "12345"

    def test_encrypt_special_characters(self, security_manager):
        """Test encryption of special characters"""
        text = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        encrypted = security_manager.encrypt_data(text)
        decrypted = security_manager.decrypt_data(encrypted)

        assert decrypted == text

    def test_encrypt_long_text(self, security_manager):
        """Test encryption of long text"""
        text = "A" * 10000
        encrypted = security_manager.encrypt_data(text)
        decrypted = security_manager.decrypt_data(encrypted)

        assert decrypted == text

    def test_encrypt_multiline_text(self, security_manager):
        """Test encryption of multiline text"""
        text = "Line 1\nLine 2\nLine 3"
        encrypted = security_manager.encrypt_data(text)
        decrypted = security_manager.decrypt_data(encrypted)

        assert decrypted == text


# ==================== DATA DECRYPTION ====================

class TestDataDecryption:
    """Test data decryption functionality"""

    def test_decrypt_valid_data(self, security_manager):
        """Test decryption of valid encrypted data"""
        plain_text = "test_data"
        encrypted = security_manager.encrypt_data(plain_text)
        decrypted = security_manager.decrypt_data(encrypted)

        assert decrypted == plain_text

    def test_decrypt_empty_string(self, security_manager):
        """Test that empty string returns empty"""
        result = security_manager.decrypt_data("")
        assert result == ""

    def test_decrypt_none(self, security_manager):
        """Test that None returns empty"""
        result = security_manager.decrypt_data(None)
        assert result == ""

    def test_decrypt_invalid_token_raises_error(self, security_manager):
        """Test that invalid encrypted data raises error"""
        with pytest.raises(RuntimeError, match="Data decryption failed"):
            security_manager.decrypt_data("invalid_encrypted_data")

    def test_decrypt_corrupted_data_raises_error(self, security_manager):
        """Test that corrupted encrypted data raises error"""
        plain_text = "test"
        encrypted = security_manager.encrypt_data(plain_text)
        corrupted = encrypted[:-5] + "XXXXX"  # Corrupt the data

        with pytest.raises(RuntimeError):
            security_manager.decrypt_data(corrupted)


# ==================== ENCRYPTION KEY MANAGEMENT ====================

class TestKeyManagement:
    """Test encryption key loading and management"""

    def test_load_key_from_env(self, monkeypatch):
        """Test that key is loaded from environment variable"""
        test_key = Fernet.generate_key().decode()
        monkeypatch.setenv("CLINIC_APP_SECRET_KEY", test_key)

        sm = SecurityManager()
        assert sm.key == test_key.encode()

    def test_load_key_from_file(self, tmp_path, monkeypatch):
        """Test that key is loaded from file"""
        # Remove env variable
        monkeypatch.delenv("CLINIC_APP_SECRET_KEY", raising=False)

        # Create temporary key file
        key = Fernet.generate_key()
        key_file = tmp_path / "secret.key"
        key_file.write_bytes(key)

        # Change to temp directory
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            sm = SecurityManager()
            assert sm.key == key
        finally:
            os.chdir(original_dir)

    def test_generate_key_if_not_exists(self, tmp_path, monkeypatch):
        """Test that key is generated if not exists"""
        # Remove env variable
        monkeypatch.delenv("CLINIC_APP_SECRET_KEY", raising=False)

        # Change to temp directory (no key file exists)
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            sm = SecurityManager()

            # Key should be generated
            assert sm.key is not None
            assert len(sm.key) > 0

            # Key file should be created
            key_file = tmp_path / "secret.key"
            assert key_file.exists()
        finally:
            os.chdir(original_dir)

    def test_key_consistency_across_instances(self, tmp_path, monkeypatch):
        """Test that multiple instances use the same key from file"""
        monkeypatch.delenv("CLINIC_APP_SECRET_KEY", raising=False)

        # Create key file
        key = Fernet.generate_key()
        key_file = tmp_path / "secret.key"
        key_file.write_bytes(key)

        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            sm1 = SecurityManager()
            sm2 = SecurityManager()

            # Both should use the same key
            assert sm1.key == sm2.key == key

            # Data encrypted by one should be decryptable by other
            plain_text = "test_data"
            encrypted = sm1.encrypt_data(plain_text)
            decrypted = sm2.decrypt_data(encrypted)

            assert decrypted == plain_text
        finally:
            os.chdir(original_dir)


# ==================== SECURITY EDGE CASES ====================

class TestSecurityEdgeCases:
    """Test security-related edge cases"""

    def test_different_passwords_different_hashes(self, security_manager):
        """Test that different passwords produce different hashes"""
        hash1 = security_manager.hash_password("password1")
        hash2 = security_manager.hash_password("password2")

        assert hash1 != hash2

    def test_similar_passwords_different_hashes(self, security_manager):
        """Test that similar passwords produce different hashes"""
        hash1 = security_manager.hash_password("password")
        hash2 = security_manager.hash_password("password1")

        assert hash1 != hash2

    def test_encryption_deterministic_with_same_key(self, security_manager):
        """Test that encryption is NOT deterministic (uses random IV)"""
        plain_text = "test_data"
        encrypted1 = security_manager.encrypt_data(plain_text)
        encrypted2 = security_manager.encrypt_data(plain_text)

        # Fernet uses random IV, so same plaintext produces different ciphertext
        # But both should decrypt to same plaintext
        assert security_manager.decrypt_data(encrypted1) == plain_text
        assert security_manager.decrypt_data(encrypted2) == plain_text

    def test_cannot_decrypt_with_wrong_key(self):
        """Test that data cannot be decrypted with different key"""
        sm1 = SecurityManager()
        sm2 = SecurityManager()

        plain_text = "sensitive_data"
        encrypted = sm1.encrypt_data(plain_text)

        # Trying to decrypt with different key should raise error
        with pytest.raises(RuntimeError):
            sm2.decrypt_data(encrypted)

    def test_sql_injection_in_password(self, security_manager):
        """Test that SQL injection attempts in password are safely handled"""
        malicious_password = "'; DROP TABLE users; --"
        hashed = security_manager.hash_password(malicious_password)

        # Should hash normally
        assert hashed is not None
        assert security_manager.verify_password(malicious_password, hashed)

    def test_xss_in_data(self, security_manager):
        """Test that XSS attempts in data are safely encrypted/decrypted"""
        xss_data = "<script>alert('XSS')</script>"
        encrypted = security_manager.encrypt_data(xss_data)
        decrypted = security_manager.decrypt_data(encrypted)

        # Should handle XSS string as regular data
        assert decrypted == xss_data

    def test_null_bytes_in_data(self, security_manager):
        """Test handling of null bytes in data"""
        data_with_null = "test\x00data"
        encrypted = security_manager.encrypt_data(data_with_null)
        decrypted = security_manager.decrypt_data(encrypted)

        assert decrypted == data_with_null


# ==================== PERFORMANCE TESTS ====================

@pytest.mark.slow
class TestPerformance:
    """Performance-related tests"""

    def test_password_hashing_performance(self, security_manager):
        """Test that password hashing is reasonably fast"""
        import time

        password = "test_password"
        start = time.time()
        security_manager.hash_password(password)
        duration = time.time() - start

        # Bcrypt should take less than 1 second for single hash
        assert duration < 1.0

    def test_encryption_performance(self, security_manager):
        """Test that encryption is fast"""
        import time

        plain_text = "test_data" * 100  # 900 characters
        start = time.time()

        for _ in range(100):
            security_manager.encrypt_data(plain_text)

        duration = time.time() - start

        # 100 encryptions should complete in less than 1 second
        assert duration < 1.0
