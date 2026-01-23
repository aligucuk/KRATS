"""
Comprehensive tests for utils/encryption_manager.py

Tests cover:
- Encryption key initialization (env, settings, generated)
- Data encryption (various data types, edge cases)
- Data decryption (roundtrip, errors)
- Invalid token handling
- Key management and configuration
"""
import pytest
import os
from cryptography.fernet import Fernet, InvalidToken

from utils.encryption_manager import EncryptionManager


# ==================== KEY INITIALIZATION ====================

class TestKeyInitialization:
    """Test encryption key initialization"""

    def test_init_with_explicit_key(self):
        """Test initialization with explicitly provided key"""
        test_key = Fernet.generate_key().decode()
        em = EncryptionManager(key=test_key)

        assert em.key == test_key.encode()
        assert em.cipher is not None

    def test_init_with_bytes_key(self):
        """Test initialization with bytes key"""
        test_key = Fernet.generate_key()
        em = EncryptionManager(key=test_key)

        assert em.key == test_key

    def test_init_with_env_key(self, monkeypatch):
        """Test that key is loaded from environment if not provided"""
        test_key = Fernet.generate_key().decode()
        monkeypatch.setenv("ENCRYPTION_KEY", test_key)

        # Mock settings to not provide a key
        from config import settings
        monkeypatch.setattr(settings, "ENCRYPTION_KEY", test_key)

        em = EncryptionManager()
        assert em.key == test_key.encode()

    def test_init_generates_key_if_not_available(self, monkeypatch):
        """Test that key is generated if not available"""
        # Mock settings to not provide a key
        from config import settings
        monkeypatch.setattr(settings, "ENCRYPTION_KEY", None)

        em = EncryptionManager()

        # Should have generated a key
        assert em.key is not None
        assert len(em.key) > 0

    def test_cipher_initialized_correctly(self, encryption_manager):
        """Test that Fernet cipher is initialized"""
        assert encryption_manager.cipher is not None
        assert isinstance(encryption_manager.cipher, Fernet)


# ==================== ENCRYPTION ====================

class TestEncryption:
    """Test data encryption functionality"""

    def test_encrypt_basic_string(self, encryption_manager):
        """Test basic string encryption"""
        plain_text = "test_data"
        encrypted = encryption_manager.encrypt(plain_text)

        assert encrypted is not None
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
        assert encrypted != plain_text

    def test_encrypt_turkish_characters(self, encryption_manager):
        """Test encryption of Turkish characters"""
        text = "Şişli İstanbul Çağlayan Öğrenci Ümit Ğ"
        encrypted = encryption_manager.encrypt(text)

        assert encrypted is not None
        assert encrypted != text

    def test_encrypt_numbers(self, encryption_manager):
        """Test encryption of numeric data"""
        number = 12345
        encrypted = encryption_manager.encrypt(str(number))

        assert encrypted is not None

    def test_encrypt_special_characters(self, encryption_manager):
        """Test encryption of special characters"""
        text = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
        encrypted = encryption_manager.encrypt(text)

        assert encrypted is not None

    def test_encrypt_empty_string(self, encryption_manager):
        """Test that empty string returns empty"""
        result = encryption_manager.encrypt("")
        assert result == ""

    def test_encrypt_none(self, encryption_manager):
        """Test that None returns empty"""
        result = encryption_manager.encrypt(None)
        assert result == ""

    def test_encrypt_whitespace(self, encryption_manager):
        """Test encryption of whitespace"""
        text = "   "
        encrypted = encryption_manager.encrypt(text)

        assert encrypted is not None
        assert encrypted != text

    def test_encrypt_multiline(self, encryption_manager):
        """Test encryption of multiline text"""
        text = "Line 1\nLine 2\nLine 3"
        encrypted = encryption_manager.encrypt(text)

        assert encrypted is not None

    def test_encrypt_long_text(self, encryption_manager):
        """Test encryption of long text"""
        text = "A" * 10000
        encrypted = encryption_manager.encrypt(text)

        assert encrypted is not None

    def test_encrypt_unicode(self, encryption_manager):
        """Test encryption of various unicode characters"""
        text = "Hello 世界 مرحبا мир 🌍"
        encrypted = encryption_manager.encrypt(text)

        assert encrypted is not None

    def test_encrypt_json_like_string(self, encryption_manager):
        """Test encryption of JSON-like string"""
        text = '{"name": "Ahmet", "age": 30}'
        encrypted = encryption_manager.encrypt(text)

        assert encrypted is not None

    def test_encrypt_sql_injection(self, encryption_manager):
        """Test encryption of SQL injection attempt"""
        text = "'; DROP TABLE users; --"
        encrypted = encryption_manager.encrypt(text)

        assert encrypted is not None

    def test_encrypt_xss_attempt(self, encryption_manager):
        """Test encryption of XSS attempt"""
        text = "<script>alert('XSS')</script>"
        encrypted = encryption_manager.encrypt(text)

        assert encrypted is not None


# ==================== DECRYPTION ====================

class TestDecryption:
    """Test data decryption functionality"""

    def test_decrypt_valid_data(self, encryption_manager):
        """Test decryption of valid encrypted data"""
        plain_text = "test_data"
        encrypted = encryption_manager.encrypt(plain_text)
        decrypted = encryption_manager.decrypt(encrypted)

        assert decrypted == plain_text

    def test_decrypt_roundtrip(self, encryption_manager):
        """Test encryption/decryption roundtrip"""
        original = "sensitive_information"
        encrypted = encryption_manager.encrypt(original)
        decrypted = encryption_manager.decrypt(encrypted)

        assert decrypted == original

    def test_decrypt_turkish_characters(self, encryption_manager):
        """Test decryption of Turkish characters"""
        text = "Şişli İstanbul Çağlayan"
        encrypted = encryption_manager.encrypt(text)
        decrypted = encryption_manager.decrypt(text)

        assert decrypted == text

    def test_decrypt_empty_string(self, encryption_manager):
        """Test that empty string returns empty"""
        result = encryption_manager.decrypt("")
        assert result == ""

    def test_decrypt_none(self, encryption_manager):
        """Test that None returns empty"""
        result = encryption_manager.decrypt(None)
        assert result == ""

    def test_decrypt_invalid_token_raises_error(self, encryption_manager):
        """Test that invalid token raises RuntimeError"""
        with pytest.raises(RuntimeError, match="invalid token"):
            encryption_manager.decrypt("invalid_encrypted_data")

    def test_decrypt_corrupted_data_raises_error(self, encryption_manager):
        """Test that corrupted data raises error"""
        plain_text = "test"
        encrypted = encryption_manager.encrypt(plain_text)
        corrupted = encrypted[:-5] + "XXXXX"

        with pytest.raises(RuntimeError):
            encryption_manager.decrypt(corrupted)

    def test_decrypt_with_wrong_key_raises_error(self, test_encryption_key):
        """Test that decryption with wrong key raises error"""
        em1 = EncryptionManager(key=test_encryption_key.decode())
        em2 = EncryptionManager(key=Fernet.generate_key().decode())

        plain_text = "secret"
        encrypted = em1.encrypt(plain_text)

        with pytest.raises(RuntimeError):
            em2.decrypt(encrypted)

    def test_decrypt_multiple_times(self, encryption_manager):
        """Test that same encrypted data can be decrypted multiple times"""
        plain_text = "test_data"
        encrypted = encryption_manager.encrypt(plain_text)

        for _ in range(10):
            decrypted = encryption_manager.decrypt(encrypted)
            assert decrypted == plain_text


# ==================== ROUNDTRIP INTEGRITY ====================

class TestRoundtripIntegrity:
    """Test encryption/decryption roundtrip integrity"""

    @pytest.mark.parametrize("text", [
        "simple text",
        "Türkçe karakterler: şğüöçİĞÜÖÇŞ",
        "Numbers: 1234567890",
        "Special: !@#$%^&*()_+-=[]{}|;:,.<>?",
        "Email: test@example.com",
        "Phone: +90 555 123 45 67",
        "TC: 12345678901",
        "Multi\nLine\nText",
        "Tab\tSeparated\tValues",
        "Unicode: 世界 مرحبا мир 🌍",
        "",  # Empty after stripping
        "   ",  # Whitespace
        "A" * 1000,  # Long text
    ])
    def test_roundtrip_various_inputs(self, encryption_manager, text):
        """Test roundtrip integrity with various inputs"""
        if not text or not text.strip():
            # Empty strings should return empty
            encrypted = encryption_manager.encrypt(text)
            if text == "":
                assert encrypted == ""
            else:
                decrypted = encryption_manager.decrypt(encrypted)
                assert decrypted == text
        else:
            encrypted = encryption_manager.encrypt(text)
            decrypted = encryption_manager.decrypt(encrypted)
            assert decrypted == text

    def test_roundtrip_patient_data(self, encryption_manager):
        """Test roundtrip with patient data examples"""
        patient_data = {
            "tc_no": "12345678901",
            "phone": "5551234567",
            "email": "ahmet@example.com",
            "address": "İstanbul, Şişli, Osmanbey Mahallesi"
        }

        for key, value in patient_data.items():
            encrypted = encryption_manager.encrypt(value)
            decrypted = encryption_manager.decrypt(encrypted)
            assert decrypted == value, f"Failed for {key}"

    def test_roundtrip_preserves_type(self, encryption_manager):
        """Test that roundtrip preserves string type"""
        text = "test_data"
        encrypted = encryption_manager.encrypt(text)
        decrypted = encryption_manager.decrypt(encrypted)

        assert isinstance(decrypted, str)
        assert isinstance(encrypted, str)


# ==================== KEY MANAGEMENT ====================

class TestKeyManagement:
    """Test encryption key management"""

    def test_same_key_consistent_decryption(self, test_encryption_key):
        """Test that same key produces consistent decryption"""
        em1 = EncryptionManager(key=test_encryption_key.decode())
        em2 = EncryptionManager(key=test_encryption_key.decode())

        plain_text = "test_data"
        encrypted = em1.encrypt(plain_text)
        decrypted = em2.decrypt(encrypted)

        assert decrypted == plain_text

    def test_different_keys_cannot_decrypt(self):
        """Test that different keys cannot decrypt each other's data"""
        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()

        em1 = EncryptionManager(key=key1.decode())
        em2 = EncryptionManager(key=key2.decode())

        plain_text = "secret"
        encrypted = em1.encrypt(plain_text)

        with pytest.raises(RuntimeError):
            em2.decrypt(encrypted)

    def test_key_format_validation(self):
        """Test that invalid key format raises error"""
        with pytest.raises(Exception):  # Fernet will raise ValueError
            EncryptionManager(key="invalid_key_format")


# ==================== EDGE CASES ====================

class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_encrypt_very_long_string(self, encryption_manager):
        """Test encryption of very long string"""
        text = "A" * 100000  # 100KB
        encrypted = encryption_manager.encrypt(text)
        decrypted = encryption_manager.decrypt(encrypted)

        assert decrypted == text

    def test_encrypt_binary_like_string(self, encryption_manager):
        """Test encryption of binary-like string"""
        text = "\x00\x01\x02\x03\x04\x05"
        encrypted = encryption_manager.encrypt(text)
        decrypted = encryption_manager.decrypt(encrypted)

        assert decrypted == text

    def test_encrypt_newlines_and_tabs(self, encryption_manager):
        """Test encryption of strings with newlines and tabs"""
        text = "Line1\nLine2\tTabbed"
        encrypted = encryption_manager.encrypt(text)
        decrypted = encryption_manager.decrypt(encrypted)

        assert decrypted == text

    def test_encrypt_repeated_characters(self, encryption_manager):
        """Test encryption of repeated characters"""
        text = "aaaaaaaaaa"
        encrypted = encryption_manager.encrypt(text)
        decrypted = encryption_manager.decrypt(encrypted)

        assert decrypted == text

    def test_multiple_encryptions_different_results(self, encryption_manager):
        """Test that multiple encryptions of same data produce different ciphertext"""
        text = "test_data"
        encrypted1 = encryption_manager.encrypt(text)
        encrypted2 = encryption_manager.encrypt(text)

        # Fernet uses random IV, so ciphertexts should be different
        # This is a security feature to prevent pattern analysis
        assert encrypted1 != encrypted2

        # But both should decrypt to same plaintext
        assert encryption_manager.decrypt(encrypted1) == text
        assert encryption_manager.decrypt(encrypted2) == text


# ==================== ERROR HANDLING ====================

class TestErrorHandling:
    """Test error handling"""

    def test_decrypt_invalid_base64(self, encryption_manager):
        """Test decryption of invalid base64 string"""
        with pytest.raises(RuntimeError):
            encryption_manager.decrypt("not-valid-base64!")

    def test_decrypt_valid_base64_invalid_token(self, encryption_manager):
        """Test decryption of valid base64 but invalid Fernet token"""
        import base64
        invalid_token = base64.urlsafe_b64encode(b"invalid_data").decode()

        with pytest.raises(RuntimeError):
            encryption_manager.decrypt(invalid_token)

    def test_encrypt_raises_on_cipher_error(self, encryption_manager, monkeypatch):
        """Test that encryption raises RuntimeError on cipher error"""
        def mock_encrypt(*args, **kwargs):
            raise Exception("Mock encryption error")

        monkeypatch.setattr(encryption_manager.cipher, "encrypt", mock_encrypt)

        with pytest.raises(RuntimeError, match="Encryption failed"):
            encryption_manager.encrypt("test")


# ==================== SECURITY TESTS ====================

class TestSecurity:
    """Test security properties"""

    def test_encryption_is_non_deterministic(self, encryption_manager):
        """Test that encryption is non-deterministic (uses IV)"""
        text = "same_text"
        encrypted1 = encryption_manager.encrypt(text)
        encrypted2 = encryption_manager.encrypt(text)

        # Should produce different ciphertexts
        assert encrypted1 != encrypted2

    def test_encrypted_data_different_from_plaintext(self, encryption_manager):
        """Test that encrypted data doesn't contain plaintext"""
        text = "secret_password"
        encrypted = encryption_manager.encrypt(text)

        # Encrypted should not contain the plaintext
        assert text not in encrypted

    def test_cannot_decrypt_without_key(self):
        """Test that data cannot be decrypted without the correct key"""
        key1 = Fernet.generate_key()
        em1 = EncryptionManager(key=key1.decode())

        text = "secret"
        encrypted = em1.encrypt(text)

        # Create new manager without the key
        em2 = EncryptionManager()

        with pytest.raises(RuntimeError):
            em2.decrypt(encrypted)


# ==================== INTEGRATION TESTS ====================

@pytest.mark.integration
class TestIntegration:
    """Integration tests with real-world scenarios"""

    def test_patient_data_encryption_workflow(self, encryption_manager):
        """Test complete patient data encryption workflow"""
        patient_data = {
            "tc_no": "12345678901",
            "name": "Ahmet Yılmaz",
            "phone": "5551234567",
            "email": "ahmet@example.com",
            "address": "İstanbul, Şişli"
        }

        # Encrypt all fields
        encrypted_data = {
            key: encryption_manager.encrypt(value)
            for key, value in patient_data.items()
        }

        # All encrypted values should be different from original
        for key in patient_data:
            assert encrypted_data[key] != patient_data[key]

        # Decrypt all fields
        decrypted_data = {
            key: encryption_manager.decrypt(value)
            for key, value in encrypted_data.items()
        }

        # All decrypted values should match original
        assert decrypted_data == patient_data

    def test_bulk_encryption_performance(self, encryption_manager):
        """Test performance with bulk encryption"""
        import time

        data_items = [f"data_item_{i}" for i in range(1000)]

        start = time.time()
        encrypted_items = [encryption_manager.encrypt(item) for item in data_items]
        encrypt_duration = time.time() - start

        start = time.time()
        decrypted_items = [encryption_manager.decrypt(item) for item in encrypted_items]
        decrypt_duration = time.time() - start

        # Verify correctness
        assert decrypted_items == data_items

        # Performance check (should be reasonably fast)
        assert encrypt_duration < 5.0, f"Encryption took {encrypt_duration}s"
        assert decrypt_duration < 5.0, f"Decryption took {decrypt_duration}s"
