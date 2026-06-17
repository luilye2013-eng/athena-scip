"""
Athena SCIP - Configuration Management
Centralizes all environment variables and settings
"""
import os
from dotenv import load_dotenv
from typing import List

# Load environment variables from .env file
load_dotenv()

class Config:
    """Main configuration class"""
    
    # ============================================
    # Supabase Configuration
    # ============================================
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://catpprgdbvenutyyjqbx.supabase.co")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "sb_publishable_ykiqckKEQw2m8XXvX4cGnQ_5ijzb7Py")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # ============================================
    # API Server Configuration
    # ============================================
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DASHBOARD_PORT: int = int(os.getenv("DASHBOARD_PORT", "8080"))
    
    # CORS - Allow multiple origins
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    
    # ============================================
    # Security Configuration
    # ============================================
    JWT_SECRET: str = os.getenv("JWT_SECRET_KEY", "change-this-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24
    
    # ============================================
    # Logging Configuration
    # ============================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def get_supabase_url(cls) -> str:
        return cls.SUPABASE_URL
    
    @classmethod
    def get_supabase_anon_key(cls) -> str:
        return cls.SUPABASE_ANON_KEY
    
    @classmethod
    def get_supabase_service_key(cls) -> str:
        return cls.SUPABASE_SERVICE_KEY
    
    @classmethod
    def is_production(cls) -> bool:
        return os.getenv("ENVIRONMENT", "development") == "production"

# Create a single instance for import
config = Config()