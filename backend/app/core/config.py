from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(BASE_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str  # Anon key for client operations
    SUPABASE_SERVICE_KEY: str  # Service role key for admin operations
    
    # Database Configuration (SQLAlchemy / Unified)
    DATABASE_URL: Optional[str] = None
    
    # Redis Configuration
    REDIS_URL: Optional[str] = None
    
    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"
    
    # AI Configuration
    GEMINI_API_KEY: str
    AI_PRIMARY_MODEL: str = "gemini-3.5-flash"
    AI_FALLBACK_MODEL: str = "gemini-2.5-flash"
    AI_MAX_RETRIES: int = 3
    AI_TIMEOUT_SECONDS: int = 30
    
    # Webhook Security Configuration
    WEBHOOK_STRIPE_SECRET: Optional[str] = "whsec_test_stripe_secret"
    WEBHOOK_TWILIO_SECRET: Optional[str] = "whsec_test_twilio_secret"
    WEBHOOK_META_SECRET: Optional[str] = "whsec_test_meta_secret"
    WEBHOOK_META_VERIFY_TOKEN: Optional[str] = "dental_crm_meta_verify_token"
    
    # OAuth 2.0 (Google SSO) Configuration
    GOOGLE_CLIENT_ID: Optional[str] = "test-google-client-id"
    GOOGLE_CLIENT_SECRET: Optional[str] = "test-google-client-secret"
    GOOGLE_REDIRECT_URI: Optional[str] = "http://localhost:3000/auth/callback/google"
    
    # Application Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Dental CRM"
    DEBUG: bool = False
    
    @property
    def api_prefix(self) -> str:
        return self.API_V1_PREFIX.rstrip("/")

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.ALLOWED_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()

