# utils/exceptions.py

class KRATSException(Exception):
    """Base exception for KRATS application"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class DatabaseException(KRATSException):
    """Database related exceptions"""
    pass


class SecurityException(KRATSException):
    """Security related exceptions"""
    pass


class ValidationException(KRATSException):
    """Validation related exceptions"""
    pass


class LicenseException(KRATSException):
    """License related exceptions"""
    pass


class ConfigurationException(KRATSException):
    """Configuration related exceptions"""
    pass


class AuthenticationException(SecurityException):
    """Authentication failures"""
    pass


class AuthorizationException(SecurityException):
    """Authorization failures"""
    pass


class RateLimitException(KRATSException):
    """Rate limit exceeded"""
    pass


class FileProcessingException(KRATSException):
    """File processing errors"""
    pass


class IntegrationException(KRATSException):
    """Third-party integration errors"""
    pass