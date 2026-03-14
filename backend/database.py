"""
Database configuration with connection pooling.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
import logging
from dotenv import load_dotenv

ROOT_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ROOT_ENV_FILE)

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./leadengine.db")

# Connection pool settings for PostgreSQL
POOL_SIZE = 5
MAX_OVERFLOW = 10
POOL_TIMEOUT = 30
POOL_RECYCLE = 1800  # Recycle connections after 30 minutes

# Create engine with appropriate settings
if "sqlite" in DATABASE_URL:
    # SQLite settings (for local development)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )
else:
    # PostgreSQL settings with connection pooling
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT,
        pool_recycle=POOL_RECYCLE,
        pool_pre_ping=True,  # Verify connection before use
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )

# Configure session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevent lazy loading issues
)

# Base class for models
Base = declarative_base()


def get_db():
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


def _safe_db_url() -> str:
    """Return DATABASE_URL with password redacted for safe logging."""
    import re as _re
    return _re.sub(r"(://[^:]+:)[^@]+(@)", r"\1***\2", DATABASE_URL)


def check_db_connection():
    """Check if database is accessible."""
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed ({_safe_db_url()}): {e}")
        return False

