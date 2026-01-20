# config.py

import os
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv
from functools import lru_cache

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()


class Settings:
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = os.getenv("APP_NAME", "KRATS Clinical OS")
    APP_VERSION: str = os.getenv("APP_VERSION", "3.0.0")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    
    # Base Directory
    BASE_DIR: Path = BASE_DIR
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/krats.db")
    DB_ECHO: bool = os.getenv("DB_ECHO", "False").lower() == "true"
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    
    # Security
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    PASSWORD_SALT_ROUNDS: int = int(os.getenv("PASSWORD_SALT_ROUNDS", "12"))
    
    # License
    LICENSE_SECRET_KEY: str = os.getenv("LICENSE_SECRET_KEY", "")
    LICENSE_VALIDATION_URL: str = os.getenv("LICENSE_VALIDATION_URL", "")
    HARDWARE_ID_SALT: str = os.getenv("HARDWARE_ID_SALT", "")
    
    # Google Services
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_CALENDAR_ENABLED: bool = os.getenv("GOOGLE_CALENDAR_ENABLED", "False").lower() == "true"
    
    # AI Services
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    AI_DEFAULT_PROVIDER: str = os.getenv("AI_DEFAULT_PROVIDER", "gemini")
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "2000"))
    
    # E-Nabiz
    ENABIZ_ENABLED: bool = os.getenv("ENABIZ_ENABLED", "False").lower() == "true"
    ENABIZ_USS_USERNAME: str = os.getenv("ENABIZ_USS_USERNAME", "")
    ENABIZ_USS_PASSWORD: str = os.getenv("ENABIZ_USS_PASSWORD", "")
    ENABIZ_FIRM_CODE: str = os.getenv("ENABIZ_FIRM_CODE", "0000")
    ENABIZ_API_URL: str = os.getenv("ENABIZ_API_URL", "https://sys.saglik.gov.tr/SYS/SYS.asmx")
    
    # SMS
    SMS_ENABLED: bool = os.getenv("SMS_ENABLED", "False").lower() == "true"
    SMS_PROVIDER: str = os.getenv("SMS_PROVIDER", "twilio")
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    # Email
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "True").lower() == "true"
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # WhatsApp
    WHATSAPP_ENABLED: bool = os.getenv("WHATSAPP_ENABLED", "False").lower() == "true"
    WHATSAPP_CHROME_DRIVER_PATH: str = os.getenv("WHATSAPP_CHROME_DRIVER_PATH", "")
    
    # Medical News
    NEWS_ENABLED: bool = os.getenv("NEWS_ENABLED", "True").lower() == "true"
    NEWS_REFRESH_INTERVAL_MINUTES: int = int(os.getenv("NEWS_REFRESH_INTERVAL_MINUTES", "30"))
    NEWS_RETENTION_DAYS: int = int(os.getenv("NEWS_RETENTION_DAYS", "7"))
    NEWS_NOTIFICATIONS: bool = os.getenv("NEWS_NOTIFICATIONS", "True").lower() == "true"
    
    # Remote Config
    REMOTE_CONFIG_URL: str = os.getenv("REMOTE_CONFIG_URL", "")
    REMOTE_CONFIG_TIMEOUT: int = int(os.getenv("REMOTE_CONFIG_TIMEOUT", "10"))
    
    # Updates
    AUTO_UPDATE_ENABLED: bool = os.getenv("AUTO_UPDATE_ENABLED", "False").lower() == "true"
    UPDATE_CHECK_URL: str = os.getenv("UPDATE_CHECK_URL", "")
    UPDATE_DOWNLOAD_URL: str = os.getenv("UPDATE_DOWNLOAD_URL", "")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/krats.log")
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", "10485760"))
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Sentry
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", "production")
    SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0"))
    
    # Backup
    BACKUP_ENABLED: bool = os.getenv("BACKUP_ENABLED", "True").lower() == "true"
    BACKUP_DIRECTORY: str = os.getenv("BACKUP_DIRECTORY", "backups")
    BACKUP_RETENTION_DAYS: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    AUTO_BACKUP_INTERVAL_HOURS: int = int(os.getenv("AUTO_BACKUP_INTERVAL_HOURS", "24"))
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    
    # Session
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "480"))
    SESSION_COOKIE_SECURE: bool = os.getenv("SESSION_COOKIE_SECURE", "True").lower() == "true"
    SESSION_COOKIE_HTTPONLY: bool = os.getenv("SESSION_COOKIE_HTTPONLY", "True").lower() == "true"
    
    # CORS
    CORS_ALLOWED_ORIGINS: List[str] = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() == "true"
    
    # File Upload
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    ALLOWED_FILE_EXTENSIONS: List[str] = os.getenv("ALLOWED_FILE_EXTENSIONS", ".pdf,.jpg,.jpeg,.png,.docx,.xlsx").split(",")
    UPLOAD_DIRECTORY: str = os.getenv("UPLOAD_DIRECTORY", "uploads")
    
    # Timezone
    TIMEZONE: str = os.getenv("TIMEZONE", "Europe/Istanbul")
    DATE_FORMAT: str = os.getenv("DATE_FORMAT", "%d.%m.%Y")
    TIME_FORMAT: str = os.getenv("TIME_FORMAT", "%H:%M")
    DATETIME_FORMAT: str = os.getenv("DATETIME_FORMAT", "%d.%m.%Y %H:%M")
    
    # Localization
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "tr")
    SUPPORTED_LANGUAGES: List[str] = os.getenv("SUPPORTED_LANGUAGES", "tr,en,de").split(",")
    
    # Performance
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "True").lower() == "true"
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))
    CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "1000"))
    
    # 3D Model Server
    MODEL_SERVER_ENABLED: bool = os.getenv("MODEL_SERVER_ENABLED", "True").lower() == "true"
    MODEL_SERVER_PORT: int = int(os.getenv("MODEL_SERVER_PORT", "8000"))
    MODEL_SERVER_HOST: str = os.getenv("MODEL_SERVER_HOST", "localhost")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate critical settings"""
        errors = []
        
        if not cls.SECRET_KEY:
            errors.append("SECRET_KEY is required")
        
        if not cls.ENCRYPTION_KEY:
            errors.append("ENCRYPTION_KEY is required")
        
        if not cls.LICENSE_SECRET_KEY:
            errors.append("LICENSE_SECRET_KEY is required")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
    
    @classmethod
    def get_database_path(cls) -> Path:
        """Get absolute database path"""
        if cls.DATABASE_URL.startswith("sqlite:///"):
            db_path = cls.DATABASE_URL.replace("sqlite:///", "")
            if not Path(db_path).is_absolute():
                return cls.BASE_DIR / db_path
            return Path(db_path)
        return None
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        directories = [
            cls.BASE_DIR / "logs",
            cls.BASE_DIR / cls.BACKUP_DIRECTORY,
            cls.BASE_DIR / cls.UPLOAD_DIRECTORY,
            cls.BASE_DIR / "reports",
            cls.BASE_DIR / "assets",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    settings.ensure_directories()
    return settings


# Global settings instance
settings = get_settings()