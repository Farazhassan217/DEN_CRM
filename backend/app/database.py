import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .core.config import settings

logger = logging.getLogger(__name__)

# Use unified database configuration from core settings
DATABASE_URL = settings.DATABASE_URL
if not DATABASE_URL:
    logger.warning("DATABASE_URL not explicitly configured; using local SQLite fallback")
    DATABASE_URL = "sqlite:///./dental_crm_fallback.db"

# Engine configuration with health checks and pool resilience
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
