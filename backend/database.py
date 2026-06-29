"""
Database configuration and client initialization module.

This module sets up the database connections for the MedAI 3D CT Scan System:
1. Initializes the singleton Supabase client for cloud database/storage operations.
2. Sets up the SQLAlchemy engine and session maker for local/traditional relational databases.
3. Defines FastAPI dependency injection helpers for both database connections.
"""

from typing import Generator
from supabase import create_client, Client
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from backend.config import settings
from backend.utils.logger import get_logger

# Initialize logger for the database module
logger = get_logger(__name__)

# ==============================================================================
# Design Decisions & Architectural Rationale
# ==============================================================================
#
# 1. Why a Singleton Client is Used:
#    - Resource Efficiency: The Supabase client manages its own connection pool. Recreating the
#      client on every request would lead to significant overhead from repeated TCP handshakes,
#      SSL/TLS negotiations, and socket allocation. Reusing a single client instance prevents
#      exhausting system resources under high load.
#    - Consistent State: A single instance ensures that client-level configurations, headers,
#      and interceptors remain uniform across the entire application lifetime.
#    - Thread Safety: The `supabase-py` client is designed to be thread-safe for concurrent
#      request handling in asynchronous frameworks like FastAPI.
#
# 2. Why Configuration is Separated (config.py):
#    - Twelve-Factor App Principles: Separating configuration from code allows the application
#      to run in different environments (development, testing, production) without code changes,
#      driven entirely by externalized environment variables.
#    - Security: Sensitive credentials like `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_ANON_KEY`
#      must never be hardcoded. Centralizing them in `config.py` using Pydantic ensures they are
#      safely loaded, validated, and kept out of version control.
#    - Fail-Fast Startup: Centralized configuration validates settings on startup, preventing
#      runtime failures due to missing or misconfigured keys hours after deployment.
#
# 3. Why Dependency Injection (DI) is Useful:
#    - Loose Coupling: Route handlers do not need to know how the Supabase client or database
#      sessions are constructed. They simply declare them as dependencies.
#    - Testability: During testing, we can easily mock or override database connections using
#      FastAPI's `app.dependency_overrides` without modifying any route code.
#      Example:
#          app.dependency_overrides[get_supabase] = mock_supabase_client
#    - Lifecycle Management: FastAPI handles the lifecycle of dependencies (such as yielding
#      a database session, ensuring it commits/rolls back, and closing it after the request completes).
#
# ==============================================================================

# ==============================================================================
# Supabase Integration & Validation
# ==============================================================================

# Read Supabase configurations from the centralized settings
SUPABASE_URL: str = settings.SUPABASE_URL
SUPABASE_ANON_KEY: str = settings.SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY: str = settings.SUPABASE_SERVICE_ROLE_KEY

# Validate that all required environment variables are present.
# In a production environment, missing credentials should fail-fast at startup.
if not SUPABASE_URL:
    logger.critical("SUPABASE_URL is missing from environment/settings.")
    raise RuntimeError(
        "Database Configuration Error: SUPABASE_URL environment variable is required but missing."
    )

if not SUPABASE_ANON_KEY:
    logger.critical("SUPABASE_ANON_KEY (or SUPABASE_KEY) is missing from environment/settings.")
    raise RuntimeError(
        "Database Configuration Error: SUPABASE_ANON_KEY/SUPABASE_KEY environment variable is required but missing."
    )

if not SUPABASE_SERVICE_ROLE_KEY:
    logger.critical("SUPABASE_SERVICE_ROLE_KEY is missing from environment/settings.")
    raise RuntimeError(
        "Database Configuration Error: SUPABASE_SERVICE_ROLE_KEY environment variable is required but missing."
    )

try:
    logger.info("Initializing singleton Supabase client...")
    # Initialize the singleton Supabase client using the anonymous key for client-safe operations.
    # Note: If administrative/service-role level operations are needed, a separate service client
    # can be initialized using SUPABASE_SERVICE_ROLE_KEY.
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    logger.info("Supabase client initialized successfully.")
except Exception as e:
    logger.critical(f"Failed to initialize Supabase client: {e}", exc_info=True)
    raise RuntimeError(f"Database Configuration Error: Failed to initialize Supabase client: {e}") from e


def get_supabase() -> Client:
    """
    FastAPI dependency helper to retrieve the singleton Supabase client.
    
    This function can be used with FastAPI's Depends() to inject the Supabase
    client into endpoint handlers and services.
    
    Returns:
        Client: The initialized singleton Supabase client instance.
    """
    return supabase


# ==============================================================================
# SQLAlchemy Setup (For traditional relational database integration)
# ==============================================================================
# In production, you would set a DATABASE_URL env variable.
# We default to a local SQLite database for development/testing if no URL is provided.
DATABASE_URL: str = getattr(settings, "DATABASE_URL", "sqlite:///./medai_app.db")

# Create SQLAlchemy engine
# Note: connect_args={"check_same_thread": False} is only needed for SQLite.
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session.
    
    Ensures that a database connection is opened for the duration of the request
    and is guaranteed to be closed after the request is finished.
    
    Yields:
        Generator[Session, None, None]: A SQLAlchemy Session object.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
