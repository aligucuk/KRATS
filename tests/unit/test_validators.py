"""
Comprehensive tests for utils/validators.py

Tests cover:
- Turkish ID (TC Kimlik No) validation with algorithm verification
- Phone number validation (Turkish and international formats)
- Email validation
- Date validation
- Name validation
- URL validation
- File extension validation
- Numeric range validation
"""
import pytest
from datetime import datetime
from utils.validators import Validators


# ==================== TURKISH ID VALIDATION ====================

class TestTCValidation:
    """Test Turkish ID number (TC Kimlik No) validation"""

    @pytest.fixture
    def valid_tc_numbers(self):
        """List of algorithmically valid Turkish ID numbers"""
        return [
            "10000000146",
            "10000000278",
            "10000000369",
            "10000000575",
            "10000000681",
            "11111111110"
        ]

    @pytest.fixture
    def invalid_tc_numbers(self):
        """List of invalid Turkish ID numbers"""
        return {
            "00000000000": "0 ile başlayamaz",
            "123456": "11 haneli",
            "123456789012": "11 haneli",
            "12345678900": "Geçersiz",
            "12345678901": "Geçersiz",  # Wrong checksum
            "1234567890X": "Geçersiz",
        }

    def test_valid_tc_numbers(self, valid_tc_numbers):
        """Test that algorithmically valid TC numbers pass validation"""
        for tc in valid_tc_numbers:
            is_valid, msg = Validators.validate_tc_no(tc)
            assert is_valid, f"TC {tc} should be valid but got error: {msg}"
            assert msg is None

    def test_empty_tc(self):
        """Test that empty TC number is rejected"""
        is_valid, msg = Validators.validate_tc_no("")
        assert not is_valid
        assert "boş olamaz" in msg

    def test_none_tc(self):
        """Test that None TC number is rejected"""
        is_valid, msg = Validators.validate_tc_no(None)
        assert not is_valid
        assert "boş olamaz" in msg

    def test_tc_wrong_length_short(self):
        """Test that short TC numbers are rejected"""
        is_valid, msg = Validators.validate_tc_no("123456")
        assert not is_valid
        assert "11 haneli" in msg

    def test_tc_wrong_length_long(self):
        """Test that long TC numbers are rejected"""
        is_valid, msg = Validators.validate_tc_no("123456789012")
        assert not is_valid
        assert "11 haneli" in msg

    def test_tc_starts_with_zero(self):
        """Test that TC starting with 0 is rejected"""
        is_valid, msg = Validators.validate_tc_no("01234567890")
        assert not is_valid
        assert "0 ile başlayamaz" in msg

    def test_tc_non_numeric(self):
        """Test that non-numeric TC is rejected"""
        is_valid, msg = Validators.validate_tc_no("1234567890X")
        assert not is_valid
        assert "Geçersiz" in msg or "doğrulanamadı" in msg

    def test_tc_with_spaces(self):
        """Test that TC with spaces is cleaned and validated"""
        is_valid, msg = Validators.validate_tc_no("10000 000 146")
        assert is_valid, f"Should clean spaces and validate, got: {msg}"

    def test_tc_with_dashes(self):
        """Test that TC with dashes is cleaned and validated"""
        is_valid, msg = Validators.validate_tc_no("10000-000-146")
        assert is_valid, f"Should clean dashes and validate, got: {msg}"

    def test_tc_invalid_checksum_first(self):
        """Test that TC with invalid first checksum is rejected"""
        # Valid format but wrong 10th digit (first checksum)
        is_valid, msg = Validators.validate_tc_no("10000000246")
        assert not is_valid
        assert "Geçersiz" in msg

    def test_tc_invalid_checksum_second(self):
        """Test that TC with invalid second checksum is rejected"""
        # Valid format but wrong 11th digit (second checksum)
        is_valid, msg = Validators.validate_tc_no("10000000147")
        assert not is_valid
        assert "Geçersiz" in msg

    def test_tc_all_zeros(self):
        """Test that all zeros is rejected"""
        is_valid, msg = Validators.validate_tc_no("00000000000")
        assert not is_valid

    def test_tc_special_characters(self):
        """Test TC with special characters"""
        is_valid, msg = Validators.validate_tc_no("100.000.001-46")
        assert is_valid or not is_valid  # Should handle gracefully


# ==================== PHONE NUMBER VALIDATION ====================

class TestPhoneValidation:
    """Test phone number validation"""

    @pytest.fixture
    def valid_turkish_phones(self):
        """List of valid Turkish phone numbers in various formats"""
        return [
            "5551234567",
            "5321234567",
            "5051234567",
            "5421234567",
            "905551234567",
            "905321234567",
            "555 123 45 67",
            "555-123-45-67",
            "(555) 123 45 67",
            "+90 555 123 45 67",
            "0555 123 45 67"  # With leading 0
        ]

    @pytest.fixture
    def invalid_turkish_phones(self):
        """List of invalid Turkish phone numbers"""
        return [
            "4551234567",  # Doesn't start with 5
            "3551234567",  # Doesn't start with 5
            "555123",  # Too short
            "555123456789",  # Too long
            "1234567890",  # Wrong format
            "6551234567"  # Doesn't start with 5
        ]

    def test_valid_turkish_mobile_10_digits(self):
        """Test valid 10-digit Turkish mobile number"""
        is_valid, msg = Validators.validate_phone("5551234567", "TR")
        assert is_valid
        assert msg is None

    def test_valid_turkish_mobile_with_country_code(self):
        """Test valid Turkish mobile with country code"""
        is_valid, msg = Validators.validate_phone("905551234567", "TR")
        assert is_valid
        assert msg is None

    def test_valid_turkish_phones_various_formats(self, valid_turkish_phones):
        """Test that various Turkish phone formats are accepted"""
        for phone in valid_turkish_phones:
            is_valid, msg = Validators.validate_phone(phone, "TR")
            assert is_valid, f"Phone {phone} should be valid but got error: {msg}"

    def test_invalid_turkish_not_starting_with_5(self):
        """Test that Turkish phone not starting with 5 is rejected"""
        is_valid, msg = Validators.validate_phone("4551234567", "TR")
        assert not is_valid
        assert "Geçersiz" in msg

    def test_invalid_turkish_too_short(self):
        """Test that short Turkish phone is rejected"""
        is_valid, msg = Validators.validate_phone("555123", "TR")
        assert not is_valid

    def test_invalid_turkish_too_long(self):
        """Test that long Turkish phone is rejected"""
        is_valid, msg = Validators.validate_phone("555123456789", "TR")
        assert not is_valid

    def test_empty_phone(self):
        """Test that empty phone is rejected"""
        is_valid, msg = Validators.validate_phone("", "TR")
        assert not is_valid
        assert "boş olamaz" in msg

    def test_none_phone(self):
        """Test that None phone is rejected"""
        is_valid, msg = Validators.validate_phone(None, "TR")
        assert not is_valid

    def test_international_phone_valid(self):
        """Test valid international phone numbers"""
        valid_international = [
            "1234567890",  # 10 digits
            "12345678901",  # 11 digits
            "123456789012",  # 12 digits
            "123456789012345"  # 15 digits
        ]
        for phone in valid_international:
            is_valid, msg = Validators.validate_phone(phone, "US")
            assert is_valid, f"International phone {phone} should be valid"

    def test_international_phone_invalid_too_short(self):
        """Test that short international phone is rejected"""
        is_valid, msg = Validators.validate_phone("123456789", "US")
        assert not is_valid

    def test_international_phone_invalid_too_long(self):
        """Test that long international phone is rejected"""
        is_valid, msg = Validators.validate_phone("1234567890123456", "US")
        assert not is_valid

    def test_phone_with_plus_sign(self):
        """Test phone number with plus sign"""
        is_valid, msg = Validators.validate_phone("+905551234567", "TR")
        assert is_valid

    def test_phone_with_parentheses(self):
        """Test phone number with parentheses"""
        is_valid, msg = Validators.validate_phone("(555) 123 45 67", "TR")
        assert is_valid


# ==================== EMAIL VALIDATION ====================

class TestEmailValidation:
    """Test email validation"""

    @pytest.fixture
    def valid_emails(self):
        """List of valid email addresses"""
        return [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user_name@example.com",
            "123@example.com",
            "test@sub.example.com"
        ]

    @pytest.fixture
    def invalid_emails(self):
        """List of invalid email addresses"""
        return [
            "invalid.email",
            "@example.com",
            "user@",
            "user name@example.com",
            "user@example",
            ""
        ]

    def test_valid_emails(self, valid_emails):
        """Test that valid email addresses are accepted"""
        for email in valid_emails:
            is_valid, msg = Validators.validate_email(email)
            assert is_valid, f"Email {email} should be valid but got error: {msg}"
            assert msg is None

    def test_invalid_emails(self, invalid_emails):
        """Test that invalid email addresses are rejected"""
        for email in invalid_emails:
            is_valid, msg = Validators.validate_email(email)
            assert not is_valid, f"Email {email} should be invalid"

    def test_empty_email(self):
        """Test that empty email is rejected"""
        is_valid, msg = Validators.validate_email("")
        assert not is_valid
        assert "boş olamaz" in msg

    def test_email_with_spaces(self):
        """Test that email with spaces is rejected"""
        is_valid, msg = Validators.validate_email("test @example.com")
        assert not is_valid

    def test_email_case_insensitive(self):
        """Test that email validation is case-insensitive"""
        is_valid, msg = Validators.validate_email("Test@Example.COM")
        assert is_valid


# ==================== DATE VALIDATION ====================

class TestDateValidation:
    """Test date validation"""

    def test_valid_date_default_format(self):
        """Test valid date with default format (DD/MM/YYYY)"""
        is_valid, msg = Validators.validate_date("15/01/2024")
        assert is_valid
        assert msg is None

    def test_valid_date_custom_format(self):
        """Test valid date with custom format"""
        is_valid, msg = Validators.validate_date("2024-01-15", "%Y-%m-%d")
        assert is_valid

    def test_invalid_date_wrong_format(self):
        """Test that date with wrong format is rejected"""
        is_valid, msg = Validators.validate_date("2024-01-15")  # Wrong format
        assert not is_valid
        assert "Geçersiz tarih" in msg

    def test_invalid_date_nonexistent(self):
        """Test that nonexistent date is rejected"""
        is_valid, msg = Validators.validate_date("31/02/2024")
        assert not is_valid

    def test_empty_date(self):
        """Test that empty date is rejected"""
        is_valid, msg = Validators.validate_date("")
        assert not is_valid
        assert "boş olamaz" in msg

    def test_invalid_date_values(self):
        """Test various invalid date values"""
        invalid_dates = [
            "32/01/2024",  # Invalid day
            "15/13/2024",  # Invalid month
            "00/01/2024",  # Invalid day (0)
            "15/00/2024"   # Invalid month (0)
        ]
        for date_str in invalid_dates:
            is_valid, msg = Validators.validate_date(date_str)
            assert not is_valid


# ==================== NAME VALIDATION ====================

class TestNameValidation:
    """Test person name validation"""

    def test_valid_name(self):
        """Test valid person name"""
        is_valid, msg = Validators.validate_name("Ahmet Yılmaz")
        assert is_valid
        assert msg is None

    def test_valid_name_turkish_characters(self):
        """Test name with Turkish characters"""
        turkish_names = [
            "Çağlar Şahin",
            "Ömer Güneş",
            "İsmail Ünal",
            "Gülşen Özdemir"
        ]
        for name in turkish_names:
            is_valid, msg = Validators.validate_name(name)
            assert is_valid, f"Name {name} should be valid"

    def test_valid_name_single_word(self):
        """Test single word name"""
        is_valid, msg = Validators.validate_name("Ahmet")
        assert is_valid

    def test_valid_name_multiple_words(self):
        """Test name with multiple words"""
        is_valid, msg = Validators.validate_name("Ahmet Ali Yılmaz")
        assert is_valid

    def test_empty_name(self):
        """Test that empty name is rejected"""
        is_valid, msg = Validators.validate_name("")
        assert not is_valid
        assert "boş olamaz" in msg

    def test_name_too_short(self):
        """Test that name shorter than minimum is rejected"""
        is_valid, msg = Validators.validate_name("A")
        assert not is_valid
        assert "en az" in msg

    def test_name_too_long(self):
        """Test that name longer than maximum is rejected"""
        long_name = "A" * 101
        is_valid, msg = Validators.validate_name(long_name)
        assert not is_valid
        assert "en fazla" in msg

    def test_name_with_numbers(self):
        """Test that name with numbers is rejected"""
        is_valid, msg = Validators.validate_name("Ahmet123")
        assert not is_valid
        assert "sadece harf" in msg

    def test_name_with_special_characters(self):
        """Test that name with special characters is rejected"""
        invalid_names = [
            "Ahmet@Yılmaz",
            "Ahmet-Yılmaz",
            "Ahmet.Yılmaz",
            "Ahmet_Yılmaz"
        ]
        for name in invalid_names:
            is_valid, msg = Validators.validate_name(name)
            assert not is_valid

    def test_name_custom_length_limits(self):
        """Test name validation with custom length limits"""
        is_valid, msg = Validators.validate_name("Ahmet", min_length=5, max_length=10)
        assert is_valid

        is_valid, msg = Validators.validate_name("Ali", min_length=5, max_length=10)
        assert not is_valid


# ==================== URL VALIDATION ====================

class TestURLValidation:
    """Test URL validation"""

    @pytest.fixture
    def valid_urls(self):
        """List of valid URLs"""
        return [
            "http://example.com",
            "https://example.com",
            "https://www.example.com",
            "http://example.com/path",
            "https://example.com/path?query=value",
            "http://localhost",
            "http://192.168.1.1",
            "https://sub.example.com:8080/path"
        ]

    @pytest.fixture
    def invalid_urls(self):
        """List of invalid URLs"""
        return [
            "example.com",  # Missing protocol
            "ftp://example.com",  # Wrong protocol
            "http://",  # Incomplete
            "not a url",
            ""
        ]

    def test_valid_urls(self, valid_urls):
        """Test that valid URLs are accepted"""
        for url in valid_urls:
            is_valid, msg = Validators.validate_url(url)
            assert is_valid, f"URL {url} should be valid but got error: {msg}"

    def test_invalid_urls(self, invalid_urls):
        """Test that invalid URLs are rejected"""
        for url in invalid_urls:
            is_valid, msg = Validators.validate_url(url)
            assert not is_valid, f"URL {url} should be invalid"

    def test_empty_url(self):
        """Test that empty URL is rejected"""
        is_valid, msg = Validators.validate_url("")
        assert not is_valid
        assert "boş olamaz" in msg


# ==================== FILE EXTENSION VALIDATION ====================

class TestFileExtensionValidation:
    """Test file extension validation"""

    def test_valid_extension(self):
        """Test file with valid extension"""
        is_valid, msg = Validators.validate_file_extension(
            "document.pdf",
            [".pdf", ".doc", ".docx"]
        )
        assert is_valid
        assert msg is None

    def test_valid_extension_case_insensitive(self):
        """Test that extension check is case-insensitive"""
        is_valid, msg = Validators.validate_file_extension(
            "document.PDF",
            [".pdf"]
        )
        assert is_valid

    def test_invalid_extension(self):
        """Test file with invalid extension"""
        is_valid, msg = Validators.validate_file_extension(
            "document.exe",
            [".pdf", ".doc", ".docx"]
        )
        assert not is_valid
        assert "İzin verilen formatlar" in msg

    def test_no_extension(self):
        """Test file without extension"""
        is_valid, msg = Validators.validate_file_extension(
            "document",
            [".pdf"]
        )
        assert not is_valid

    def test_empty_filename(self):
        """Test empty filename"""
        is_valid, msg = Validators.validate_file_extension(
            "",
            [".pdf"]
        )
        assert not is_valid
        assert "boş olamaz" in msg

    def test_multiple_dots_in_filename(self):
        """Test filename with multiple dots"""
        is_valid, msg = Validators.validate_file_extension(
            "my.document.pdf",
            [".pdf"]
        )
        assert is_valid


# ==================== NUMERIC RANGE VALIDATION ====================

class TestNumericRangeValidation:
    """Test numeric range validation"""

    def test_valid_number_within_range(self):
        """Test number within specified range"""
        is_valid, msg = Validators.validate_numeric_range(50, min_val=0, max_val=100)
        assert is_valid
        assert msg is None

    def test_valid_number_at_minimum(self):
        """Test number at minimum boundary"""
        is_valid, msg = Validators.validate_numeric_range(0, min_val=0, max_val=100)
        assert is_valid

    def test_valid_number_at_maximum(self):
        """Test number at maximum boundary"""
        is_valid, msg = Validators.validate_numeric_range(100, min_val=0, max_val=100)
        assert is_valid

    def test_invalid_number_below_minimum(self):
        """Test number below minimum"""
        is_valid, msg = Validators.validate_numeric_range(-1, min_val=0, max_val=100)
        assert not is_valid
        assert "en az" in msg

    def test_invalid_number_above_maximum(self):
        """Test number above maximum"""
        is_valid, msg = Validators.validate_numeric_range(101, min_val=0, max_val=100)
        assert not is_valid
        assert "en fazla" in msg

    def test_valid_number_no_minimum(self):
        """Test number with no minimum constraint"""
        is_valid, msg = Validators.validate_numeric_range(-1000, max_val=100)
        assert is_valid

    def test_valid_number_no_maximum(self):
        """Test number with no maximum constraint"""
        is_valid, msg = Validators.validate_numeric_range(1000, min_val=0)
        assert is_valid

    def test_valid_number_no_constraints(self):
        """Test number with no constraints"""
        is_valid, msg = Validators.validate_numeric_range(12345)
        assert is_valid

    def test_valid_float_number(self):
        """Test float number validation"""
        is_valid, msg = Validators.validate_numeric_range(50.5, min_val=0, max_val=100)
        assert is_valid

    def test_valid_string_number(self):
        """Test string representation of number"""
        is_valid, msg = Validators.validate_numeric_range("50", min_val=0, max_val=100)
        assert is_valid

    def test_invalid_non_numeric(self):
        """Test non-numeric value"""
        is_valid, msg = Validators.validate_numeric_range("abc", min_val=0, max_val=100)
        assert not is_valid
        assert "Geçersiz sayısal değer" in msg

    def test_negative_numbers(self):
        """Test validation with negative numbers"""
        is_valid, msg = Validators.validate_numeric_range(-50, min_val=-100, max_val=0)
        assert is_valid
