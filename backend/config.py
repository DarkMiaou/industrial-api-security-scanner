"""
ⒸAngelaMos | 2025
All environment variables and constants are centralized here
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables

    All magic numbers and configuration values are defined here to avoid
    hardcoding throughout the application
    """
    model_config = SettingsConfigDict(
        env_file="../.env", env_file_encoding="utf-8", case_sensitive=True
    )

    # Application metadata
    APP_NAME: str = "IASS-OT"
    VERSION: str = "1.0.1"
    DEBUG: bool = False

    # Database configuration
    DATABASE_URL: str
    POSTGRES_USER: str = "apiuser"
    POSTGRES_PASSWORD: str = "apipass"
    POSTGRES_DB: str = "apisecurity"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Security - JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Backend server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # CORS origins (comma-separated string)
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Closed OT target. TargetPolicy verifies this exact Docker-internal URL.
    OT_TARGET_KEY: str = "ot-gateway-demo"
    OT_GATEWAY_URL: str = "http://ot-gateway-demo:8081"
    OT_GATEWAY_DISPLAY_NAME: str = "Water Pump Gateway"
    OT_DEMO_RESET_KEY: str = "local-demo-reset-key"

    # Scanner safety envelope
    SCANNER_REQUEST_BUDGET: int = 60
    SCANNER_MAX_RESPONSE_BYTES: int = 1_048_576
    SCANNER_EVIDENCE_EXCERPT_CHARS: int = 500

    # API endpoint rate limiting (incoming requests - slowapi format)
    API_RATE_LIMIT_LOGIN: str = "20/minute"
    API_RATE_LIMIT_REGISTER: str = "15/minute"
    API_RATE_LIMIT_SCAN: str = "15/minute"
    API_RATE_LIMIT_DEFAULT: str = "100/minute"

    # Pagination
    DEFAULT_PAGINATION_LIMIT: int = 20
    MAX_PAGINATION_LIMIT: int = 1000

    # Field validation constants
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 100
    EMAIL_MAX_LENGTH: int = 255
    URL_MAX_LENGTH: int = 2048

    # Scanner timeouts and limits
    SCANNER_CONNECTION_TIMEOUT: int = 3
    SCANNER_READ_TIMEOUT: int = 5

    @property
    def cors_origins_list(self) -> list[str]:
        """
        Convert comma separated CORS origins string to list
        """
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    The @lru_cache decorator ensures settings are loaded only once
    and cached for the application lifetime.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


settings = get_settings()
