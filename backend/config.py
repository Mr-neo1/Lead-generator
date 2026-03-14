"""
Application configuration with environment validation.
Uses pydantic-settings for type-safe configuration.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import List, Optional
import os

ROOT_ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


class Settings(BaseSettings):
    """Application settings with environment variable validation."""
    
    # Database
    database_url: str = Field(
        default="sqlite:///./leadengine.db",
        description="Database connection URL (PostgreSQL or SQLite)"
    )
    
    # Redis (optional for local dev)
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    use_redis: bool = Field(
        default=False,
        description="Enable Redis for task queue"
    )
    
    # API Settings
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    debug: bool = Field(default=False)
    
    # Security
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication (leave empty to disable)"
    )
    cors_origins: str = Field(
        default="https://leadscraper.freelancleadsapp.tech,http://localhost:3000",
        description="Comma-separated list of allowed CORS origins"
    )
    
    # Telegram (optional)
    telegram_bot_token: str = Field(default="")
    telegram_chat_id: str = Field(default="")
    
    # Rate limiting
    rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum API requests per minute per IP"
    )
    
    # Scraping settings
    scrape_delay_min: float = Field(
        default=1.0,
        description="Minimum delay between scraping requests (seconds)"
    )
    scrape_delay_max: float = Field(
        default=3.0,
        description="Maximum delay between scraping requests (seconds)"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retries for failed scraping tasks"
    )
    website_check_timeout: int = Field(
        default=15,
        description="HTTP timeout for website checks (seconds)"
    )
    
    # Lead scoring thresholds (customizable)
    no_website_score: int = Field(default=4)
    high_rating_score: int = Field(default=2)
    high_reviews_score: int = Field(default=1)
    has_phone_score: int = Field(default=1)
    high_rating_threshold: float = Field(default=4.0)
    high_reviews_threshold: int = Field(default=20)
    qualified_lead_min_score: int = Field(default=5)
    
    # Pagination
    default_page_size: int = Field(default=50)
    max_page_size: int = Field(default=200)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ROOT_ENV_FILE
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()
