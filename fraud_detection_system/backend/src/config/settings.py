# backend/src/config/settings.py

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings for validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # Environment
    ENV: str = "development"
    DEBUG: bool = False
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:3000"
    
    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # SQL Server
    SQLSERVER_HOST: str
    SQLSERVER_PORT: int = 1433
    SQLSERVER_DATABASE: str
    SQLSERVER_USERNAME: str
    SQLSERVER_PASSWORD: str
    SQLSERVER_DRIVER: str = "{ODBC Driver 17 for SQL Server}"
    
    # Firebird
    FIREBIRD_HOST: str = "localhost"
    FIREBIRD_PORT: int = 3050
    FIREBIRD_DATABASE: str
    FIREBIRD_USERNAME: str = "sysdba"
    FIREBIRD_PASSWORD: str
    FIREBIRD_CHARSET: str = "UTF8"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SSL: bool = False
    CACHE_TTL_SECONDS: int = 300
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE_PATH: str = "logs/fraud_detection.log"
    
    # WebSocket
    WEBSOCKET_ENABLED: bool = True
    WEBSOCKET_CORS_ALLOWED_ORIGINS: str = "*"
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "fraud-detection@company.com"
    SMTP_USE_TLS: bool = True
    
    # Fraud Detection
    FRAUD_DETECTION_ENABLED: bool = True
    FRAUD_CHECK_INTERVAL_MINUTES: int = 5
    FRAUD_SEVERITY_LEVELS: str = "LOW,MEDIUM,HIGH,CRITICAL"
    FRAUD_AUTO_BLOCK_CRITICAL: bool = False
    
    # Business Rules
    THRESHOLD_INVOICE_ROUND_AMOUNT: float = 1000
    THRESHOLD_FUEL_OVERCAPACITY_PERCENT: float = 105
    THRESHOLD_DAILY_TRANSACTIONS_LIMIT: int = 50
    THRESHOLD_NIGHT_HOURS_START: int = 22
    THRESHOLD_NIGHT_HOURS_END: int = 6
    THRESHOLD_MAX_DISCOUNT_PERCENT: float = 30
    THRESHOLD_SUSPICIOUS_MODIFICATION_HOURS: int = 2
    
    # Performance
    MAX_WORKERS: int = 4
    CONNECTION_POOL_SIZE: int = 20
    CONNECTION_POOL_OVERFLOW: int = 10
    STATEMENT_TIMEOUT_SECONDS: int = 30
    
    # Feature Flags
    FEATURE_REALTIME_MONITORING: bool = True
    FEATURE_EXPORT_REPORTS: bool = True
    FEATURE_EMAIL_ALERTS: bool = True
    FEATURE_SMS_ALERTS: bool = False
    FEATURE_AUDIT_TRAIL: bool = True
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # System Defaults
    DEFAULT_PAGINATION_SIZE: int = 20
    MAX_PAGINATION_SIZE: int = 100
    DEFAULT_TIMEZONE: str = "America/Guayaquil"
    DEFAULT_LANGUAGE: str = "es"
    DEFAULT_CURRENCY: str = "USD"
    
    @property
    def database_url(self) -> str:
        """Build SQL Server database URL."""
        return (
            f"mssql+pyodbc://{self.SQLSERVER_USERNAME}:"
            f"{self.SQLSERVER_PASSWORD}@"
            f"{self.SQLSERVER_HOST}/"
            f"{self.SQLSERVER_DATABASE}"
            f"?driver={self.SQLSERVER_DRIVER}"
        )
    
    @property
    def redis_url(self) -> str:
        """Build Redis URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def severity_levels_list(self) -> List[str]:
        """Get fraud severity levels as list."""
        return self.FRAUD_SEVERITY_LEVELS.split(",")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()